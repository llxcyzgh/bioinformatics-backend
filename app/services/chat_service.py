import json
import logging
import base64
import os
import random
import re
import subprocess
import uuid
from typing import Optional

import httpx

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models import Task, Message
from app.services.execution_service import ExecutionService
from app.services.ai_service import AIService
from app.services.parser_service import ParserService
from app.services.planner_service import PlannerService
from app.services.upload_service import UploadService
from config.llm import DASHSCOPE_API_BASE, DASHSCOPE_API_KEY, DASHSCOPE_MODEL_NAME, LLM_PARSER_TIMEOUT
from config.upload import UPLOAD_DIR
from pkg.amplicon.amplicon_tools import DATA_TYPE_NAMES
from pkg.amplicon.amplicon_tools import resolve_root_inputs
from pkg.amplicon.code_templates import generate_workflow_script
from pkg.amplicon.orchestrator import generate_orchestrator_script
from app.services.script_service import ScriptService

logger = logging.getLogger(__name__)


class ChatService:

    @staticmethod
    def _get_or_create_task(db: Session, task_id: Optional[int], task_uuid: Optional[str], project_id: int, user_id: int, task_name: str = "") -> Task:
        if task_uuid:
            task = Task.where(db, uuid=task_uuid).first()
            if not task:
                raise ValueError("Task not found")
            if task.user_id != user_id:
                raise ValueError("Forbidden")
            return task

        if task_id:
            task = Task.find(db, task_id)
            if not task:
                raise ValueError("Task not found")
            if task.user_id != user_id:
                raise ValueError("Forbidden")
            return task

        name = task_name[:50] if task_name else "New Chat"
        task = Task(
            uuid=str(uuid.uuid4()),
            name=name,
            project_id=project_id,
            user_id=user_id,
        )
        return task.save(db)

    @staticmethod
    def _ensure_sge_execd() -> None:
        """检查 SGE 执行节点 sge_execd 是否已启动；未启动则抛出明确错误。"""
        result = subprocess.run(
            ["docker", "exec", "sge-master", "bash", "-c",
             "source /opt/sge/default/common/settings.sh && ps aux | grep -v grep | grep sge_execd"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0 or not result.stdout.strip():
            raise ValueError(
                "SGE 执行节点（sge_execd）未启动，无法提交任务。"
                "请先运行：docker exec sge-master bash -c \"source /opt/sge/default/common/settings.sh && /opt/sge/bin/lx-amd64/sge_execd\""
            )

    @staticmethod
    def _build_history_dicts(history: list) -> list[dict]:
        """将 Message 列表转为 dict 列表供 parser 使用"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]

    @staticmethod
    def _analyze_images(image_paths: list[str]) -> str:
        """用多模态 LLM 解析图片，返回描述文本。"""
        if not DASHSCOPE_API_KEY or not image_paths:
            return ""

        import httpx

        content_parts = [
            {
                "type": "text",
                "text": "请仔细分析这些图片，描述其中与生物信息分析相关的所有信息，包括：数据类型、样本信息、分析结果、图表内容等。用简洁的中文描述，不超过200字。",
            }
        ]

        for path in image_paths:
            full_path = os.path.join(UPLOAD_DIR, path)
            if not os.path.exists(full_path):
                logger.warning(f"[ChatService] 图片文件不存在: {full_path}")
                continue
            ext = os.path.splitext(full_path)[1].lower()
            mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
            mime = mime_map.get(ext, "image/png")
            with open(full_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
            })
            logger.info(f"[ChatService] 已加载图片: {path} ({mime}, {len(b64)} bytes base64)")

        if len(content_parts) == 1:
            logger.warning("[ChatService] 没有可用的图片文件")
            return ""

        try:
            vl_model = os.getenv("DASHSCOPE_VL_MODEL", "qwen-vl-plus")
            logger.info(f"[ChatService] 调用视觉模型 {vl_model} 解析图片...")
            response = httpx.post(
                f"{DASHSCOPE_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
                json={
                    "model": vl_model,
                    "messages": [{"role": "user", "content": content_parts}],
                    "temperature": 0.1,
                },
                timeout=LLM_PARSER_TIMEOUT,
            )
            response.raise_for_status()
            result = response.json()
            description = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            logger.info(f"[ChatService] 图片解析成功(usage: prompt={usage.get('prompt_tokens','?')}, completion={usage.get('completion_tokens','?')}): {description}")
            return description
        except Exception as e:
            logger.warning(f"[ChatService] 图片解析失败: {type(e).__name__}: {e}")
            return ""

    @staticmethod
    def _format_data_type_names(type_ids: list[str]) -> str:
        return "、".join(DATA_TYPE_NAMES.get(t, t) for t in type_ids)

    @staticmethod
    def _get_previously_used_paths(db: Session, user_id: int) -> set[str]:
        """查询当前用户历史选择过的路径，返回排序后的 tool_ids 字符串集合"""
        user_task_ids = [t.id for t in Task.where(db, user_id=user_id).all()]
        if not user_task_ids:
            return set()

        select_msgs = (
            Message.where(db, type="select_path")
            .filter(Message.task_id.in_(user_task_ids))
            .all()
        )

        used_keys = set()
        for msg in select_msgs:
            try:
                data = json.loads(msg.data) if msg.data else {}
                tool_ids = data.get("tool_ids", [])
                if tool_ids:
                    used_keys.add(",".join(sorted(tool_ids)))
            except (json.JSONDecodeError, TypeError):
                pass
        return used_keys

    @staticmethod
    def _route_decision(parser_result: dict, content: str, history_dicts: list[dict]) -> dict:
        """根据解析结果决定回复类型"""
        available = parser_result.get("available_inputs", [])
        goals = parser_result.get("goal_types", [])

        # CASE A: 都不知道 → 澄清
        if not available and not goals:
            clarification = ParserService.generate_clarification(content, history_dicts)
            return {
                "type": "clarification",
                "content": clarification,
                "data": "",
            }

        # CASE B: 知道输入但不知道目标 → 追问目标
        if available and not goals:
            input_names = ChatService._format_data_type_names(available)
            return {
                "type": "clarification",
                "content": (
                    f"我了解到您目前拥有以下数据：{input_names}。\n\n"
                    "请问您希望进行哪些分析？例如：\n"
                    "- 物种分类注释\n"
                    "- Alpha/Beta 多样性分析\n"
                    "- 差异分析（LEfSe、T检验等）\n"
                    "- 可视化（热图、网络图、柱状图等）\n"
                    "- 功能预测\n\n"
                    "您也可以说\"全流程\"进行完整分析。"
                ),
                "data": "",
                "available_inputs": json.dumps(available, ensure_ascii=False),
            }

        # CASE C: 知道目标但不知道输入 → 追问数据
        if goals and not available:
            goal_names = ChatService._format_data_type_names(goals)
            return {
                "type": "clarification",
                "content": (
                    f"您想要进行的分析：{goal_names}。\n\n"
                    "请问您目前有什么数据？例如：\n"
                    "- 双端测序原始数据（FASTQ）\n"
                    "- FASTA 序列文件\n"
                    "- 已做完 DADA2 去噪的 ASV 表\n"
                    "- 已做完质控的序列\n\n"
                    "请描述您的数据类型，以便我为您规划分析流程。"
                ),
                "data": "",
                "goal_types": json.dumps(goals, ensure_ascii=False),
            }

        # CASE D: 都知道 → 运行规划器
        candidates = PlannerService.plan_workflow(available, goals)

        if not candidates:
            return {
                "type": "clarification",
                "content": (
                    "根据您提供的信息，暂时无法找到合适的分析方案。\n"
                    "请尝试更详细地描述您的数据类型和分析需求，或者提供更多信息。"
                ),
                "data": "",
                "available_inputs": json.dumps(available, ensure_ascii=False),
                "goal_types": json.dumps(goals, ensure_ascii=False),
            }

        best = candidates[0]
        summary_parts = []
        for i, c in enumerate(candidates):
            summary_parts.append(f"**方案{i + 1}**（{len(c['tool_chain'])}步，得分 {c['score']}）：{c['explanation']}")

        summary = "\n\n".join(summary_parts)
        input_names = ChatService._format_data_type_names(available)
        goal_names = ChatService._format_data_type_names(goals)

        return {
            "type": "workflow",
            "content": f"输入数据：{input_names}\n分析目标：{goal_names}\n\n{summary}",
            "data": "",
            "available_inputs": json.dumps(available, ensure_ascii=False),
            "goal_types": json.dumps(goals, ensure_ascii=False),
            "workflow_candidates": json.dumps(candidates, ensure_ascii=False),
        }

    @staticmethod
    def chat(
        db: Session,
        task_id: Optional[int],
        task_uuid: Optional[str],
        project_id: int,
        content: str,
        msg_type: str,
        user_id: int,
        image_ids: list[int] | None = None,
        image_filenames: list[str] | None = None,
        images: list[UploadFile] | None = None,
    ) -> dict:
        # Build task name from content or image filenames
        task_name = content.strip() if content.strip() else (image_filenames[0] if image_filenames else "")

        task = ChatService._get_or_create_task(db, task_id, task_uuid, project_id, user_id, task_name)

        # Upload inline images (after task exists so task_id is correct)
        all_image_urls = []
        if image_ids:
            for fid in image_ids:
                record = UploadService.find(db, fid, user_id)
                if record:
                    all_image_urls.append(f"/uploads/{record.file_path}")
        if images:
            for img in images:
                try:
                    record = UploadService.create(img, user_id, db, task.id)
                    all_image_urls.append(f"/uploads/{record.file_path}")
                except ValueError as e:
                    logger.warning(f"[ChatService] 图片上传失败: {e}")

        # Analyze images with multimodal LLM and merge with text
        combined_content = content
        if all_image_urls:
            # URLs are "/uploads/{user_id}/{file}", extract the relative path after /uploads/
            image_paths = [url.removeprefix("/uploads/") for url in all_image_urls]
            logger.info(f"[ChatService] 待解析图片路径: {image_paths}")
            image_description = ChatService._analyze_images(image_paths)
            if image_description:
                combined_content = f"{content}\n\n[用户上传的图片内容分析]: {image_description}" if content.strip() else f"[用户上传的图片内容分析]: {image_description}"
                logger.info(f"[ChatService] 合并后的输入: {combined_content}")

        user_message = Message(
            task_id=task.id,
            role="user",
            type=msg_type if msg_type else "text",
            content=content,
            data="",
            images=json.dumps(all_image_urls, ensure_ascii=False) if all_image_urls else "",
        )
        user_message.save(db)

        # Get conversation history
        history = (
            Message.where(db, task_id=task.id)
            .order_by(Message.id.asc())
            .all()
        )
        history_dicts = ChatService._build_history_dicts(history)

        # Parse user input (use combined content with image descriptions)
        try:
            parser_result = ParserService.parse(combined_content, history_dicts)
            logger.info(f"[ChatService] 解析结果: {parser_result}")

            # Decision routing
            ai_response = ChatService._route_decision(parser_result, combined_content, history_dicts)
        except Exception as e:
            logger.error(f"[ChatService] 解析/规划异常，回退到通用 AI: {e}")
            ai_response = AIService.generate_response(task.id, user_message, history)

        # 标注 previously_used：对比用户历史选择过的路径
        if ai_response.get("workflow_candidates"):
            try:
                candidates = json.loads(ai_response["workflow_candidates"])
                used_keys = ChatService._get_previously_used_paths(db, user_id)
                for c in candidates:
                    tool_ids = [t["id"] for t in c.get("tool_chain", []) if isinstance(t, dict) and "id" in t]
                    key = ",".join(sorted(tool_ids))
                    c["previously_used"] = key in used_keys
                ai_response["workflow_candidates"] = json.dumps(candidates, ensure_ascii=False)
            except Exception as e:
                logger.warning(f"[ChatService] previously_used 标注失败: {e}")

        # Save AI response
        ai_message = Message(
            task_id=task.id,
            role="assistant",
            type=ai_response["type"],
            content=ai_response["content"],
            data=ai_response.get("data", ""),
            images=ai_response.get("images", ""),
            available_inputs=ai_response.get("available_inputs", ""),
            goal_types=ai_response.get("goal_types", ""),
            workflow_candidates=ai_response.get("workflow_candidates", ""),
            required_files=ai_response.get("required_files", ""),
            result_content=ai_response.get("result_content", ""),
            result_files=ai_response.get("result_files", ""),
            next_steps=ai_response.get("next_steps", ""),
        )
        ai_message.save(db)

        return {
            "task": task.to_dict(),
            "message": ai_message.to_dict(),
        }

    @staticmethod
    def confirm_path(
        db: Session,
        task_uuid: str,
        project_id: int,
        candidate_id: str,
        candidate_data: str,
        user_id: int,
    ) -> dict:
        """用户确认选择分析路径 → 返回必需文件（不生成代码）"""
        task = ChatService._get_or_create_task(db, None, task_uuid, project_id, user_id)
        logger.info(f"[ChatService] 路径确认: task={task.id}, candidate={candidate_id}")

        # 解析候选方案
        try:
            candidate = json.loads(candidate_data)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid candidate data: {e}")

        tool_chain = candidate.get("tool_chain", [])
        if not tool_chain:
            raise ValueError("tool_chain is empty")

        tool_ids = [t["id"] for t in tool_chain if isinstance(t, dict) and "id" in t]
        explanation = candidate.get("explanation", "")

        # 确定必需文件
        required_files = resolve_root_inputs(tool_ids)
        logger.info(f"[ChatService] 必需文件: {[f['typeId'] for f in required_files]}")

        # 如果从原始序列数据开始，追加 metadata 文件需求
        first_inputs = required_files[0]["typeId"] if required_files else ""
        if first_inputs in ("FASTQ_PAIR", "FASTA_SEQ", "FASTQ_TRIMMED", "FASTQ_MERGED"):
            required_files.append({
                "typeId": "METADATA",
                "label": "样本信息表(metadata)",
                "description": "包含样本分组信息的元数据CSV文件",
                "extensions": [".csv", ".tsv"],
                "required": True,
            })

        # 检查路径中是否包含需要引物的步骤
        needs_primers = "amp-cutadapt" in tool_ids

        # 保存用户消息（记录选择）
        tool_names = " → ".join(t.get("name", t.get("id", "")) for t in tool_chain)
        user_message = Message(
            task_id=task.id,
            role="user",
            type="select_path",
            content=f"✅ 已选择分析方案：{explanation}\n\n工具链：{tool_names}",
            data=json.dumps({
                "selected_path": candidate,
                "tool_ids": tool_ids,
                "explanation": explanation,
            }, ensure_ascii=False),
            workflow_candidates=candidate_data,
        )
        user_message.save(db)

        # 保存助手消息（仅文件需求，不生成代码）
        file_labels = "、".join(f["label"] for f in required_files)
        file_name_list = [f["label"] for f in required_files]
        ai_message = Message(
            task_id=task.id,
            role="assistant",
            type="file_request",
            content=f"已确认分析路径（{len(tool_chain)}步）\n\n请上传以下数据文件：\n{file_labels}",
            data=json.dumps({
                "requiredFiles": file_name_list,
                "tool_ids": tool_ids,
                "needs_primers": needs_primers,
            }, ensure_ascii=False),
            required_files=json.dumps(required_files, ensure_ascii=False),
            result_content="",
            workflow_candidates=candidate_data,
        )
        ai_message.save(db)

        return {
            "task": task.to_dict(),
            "message": ai_message.to_dict(),
            "user_message": user_message.to_dict(),
        }

    @staticmethod
    def _generate_script_with_llm(
        script_parts: list,
        tool_chain: list,
        required_files: list,
    ) -> str | None:
        """用 LLM 根据工具链脚本内容生成参数衔接的完整执行脚本"""
        with open("codegen_debug.log", "a", encoding="utf-8") as _dbg:
            _dbg.write(f"--- _generate_script_with_llm ENTERED, parts={len(script_parts)} ---\n")

        if not script_parts:
            with open("codegen_debug.log", "a", encoding="utf-8") as _dbg:
                _dbg.write("--- script_parts is EMPTY, returning None ---\n")
            return None

        try:
            from config.llm import (
                DASHSCOPE_API_KEY,
                DASHSCOPE_API_BASE,
                DASHSCOPE_MODEL_NAME,
                LLM_CODEGEN_TIMEOUT,
            )

            with open("codegen_debug.log", "a", encoding="utf-8") as _dbg:
                _dbg.write(f"API_KEY: {repr(DASHSCOPE_API_KEY[:10])}... (len={len(DASHSCOPE_API_KEY)})\n")
                _dbg.write(f"API_BASE: {DASHSCOPE_API_BASE}\n")
                _dbg.write(f"MODEL: {DASHSCOPE_MODEL_NAME}\n")
                _dbg.write(f"TIMEOUT: {LLM_CODEGEN_TIMEOUT}\n")

            if not DASHSCOPE_API_KEY:
                with open("codegen_debug.log", "a", encoding="utf-8") as _dbg:
                    _dbg.write("--- API_KEY is empty, returning None ---\n")
                return None

            total_steps = len(script_parts)

            # 构建工具链描述
            chain_desc = ""
            data_flow = ""
            for i, sp in enumerate(script_parts):
                chain_desc += f"\n步骤 {i+1}/{total_steps}: {sp['name']} (tool_id={sp['tool_id']}, 类别={sp['category']})\n"
                chain_desc += f"  输入数据类型: {sp['inputs']}\n"
                chain_desc += f"  输出数据类型: {sp['outputs']}\n"
                if i > 0:
                    prev = script_parts[i - 1]
                    data_flow += f"- 步骤{i} ({prev['name']}) 的输出 → 步骤{i+1} ({sp['name']}) 的输入\n"

            # 构建需要用户上传的文件描述
            upload_desc = ""
            for rf in required_files:
                upload_desc += f"- {rf['label']} (类型ID: {rf['typeId']}, 格式: {', '.join(rf.get('extensions', []))})\n"

            # 构建每个脚本的完整内容
            scripts_content = ""
            for sp in script_parts:
                scripts_content += f"\n{'='*60}\n# 脚本: {sp['name']} ({sp['tool_id']})\n{'='*60}\n{sp['content']}\n"

            system_prompt = """你是一个生物信息分析脚本生成专家。你的任务是根据提供的工具链中每个节点的原始脚本片段，生成一个完整的、可直接执行的 bash 脚本。

## 核心要求

1. **参数衔接**：上一步的输出文件必须作为下一步的输入文件。仔细分析每个脚本的参数接口（-r1, -m, -w 等），确保数据流正确传递。

2. **工作目录**：使用 `/shared/` 作为基础工作目录。所有中间文件和输出文件都放在 `/shared/` 下。

3. **环境变量覆盖**：容器内工具路径如下，必须在脚本开头 export：
   - `export PATH=/opt/conda/bin:$PATH`
   - `RSCRIPT_BIN=/opt/conda/bin/Rscript`
   - `PERL_BIN=/usr/bin/perl`
   - `CONVERT_BIN=/opt/conda/bin/convert`
   覆盖脚本中所有默认的工具路径环境变量。对于脚本中引用的 R/Perl 辅助脚本路径（如 /newVol/...），如果不存在则在脚本开头用 `MODULE_ENV_FILE` 或直接 export 覆盖为 `/shared/lib/` 下的对应路径。如果 `/shared/lib/` 下也没有，则跳过该辅助脚本的调用并输出警告，不要报错退出。

4. **用户上传文件**：用户上传的文件存放在 `/shared/` 目录下，文件名使用上传时的原始文件名。

5. **进度输出**：每个步骤开始前输出进度信息，格式为：
   `echo "[$(date '+%Y-%m-%d %H:%M:%S')] [步骤 X/N] 正在执行: xxx"`

6. **错误处理**：使用 `set -euo pipefail`，但每个步骤用独立判断，某步骤失败时输出错误信息但不立即退出，继续执行后续步骤（除非后续步骤完全依赖前一步输出）。

7. **保留核心逻辑**：保留每个原始脚本的核心分析逻辑和参数解析代码，只调整：
   - 文件路径参数（改为变量引用）
   - 工具路径环境变量
   - 参数传递方式（从命令行参数改为变量赋值）

8. **输出格式**：只输出 bash 脚本内容，不要任何解释说明。以 #!/bin/bash 开头。

9. **简洁生成**：每个步骤的脚本要精简，去掉冗余的 usage/help 信息，只保留核心执行逻辑。"""

            user_message = f"""请根据以下工具链信息生成完整的执行脚本：

## 工具链顺序和数据流
{chain_desc}

## 数据流向
{data_flow}

## 用户需要上传的文件
{upload_desc}

## 各节点原始脚本内容（可能被截断，请根据参数接口推断完整逻辑）
{scripts_content}

请生成一个完整的 bash 脚本，将以上 {total_steps} 个分析步骤串联起来，确保参数正确衔接。"""

            prompt_size = len(system_prompt) + len(user_message)
            logger.info(f"[ChatService] 开始 LLM 代码生成: {total_steps} 个步骤, prompt={prompt_size} 字符")

            # 使用 300 秒超时，代码生成需要较长时间
            codegen_timeout = max(LLM_CODEGEN_TIMEOUT, 300)
            with open("codegen_debug.log", "a", encoding="utf-8") as _dbg:
                _dbg.write(f"About to call httpx.post, prompt_size={prompt_size}, timeout={codegen_timeout}\n")
            response = httpx.post(
                f"{DASHSCOPE_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
                json={
                    "model": DASHSCOPE_MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.3,
                },
                timeout=httpx.Timeout(codegen_timeout, connect=30.0),
            )
            response.raise_for_status()
            result = response.json()
            generated = result["choices"][0]["message"]["content"]

            # 提取 bash 脚本（去掉可能的 markdown 代码块包裹）
            if "```bash" in generated:
                generated = generated.split("```bash", 1)[1].split("```", 1)[0]
            elif "```" in generated:
                generated = generated.split("```", 1)[1].split("```", 1)[0]

            generated = generated.strip()
            logger.info(f"[ChatService] LLM 代码生成完成: {len(generated)} 字符")
            return generated

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"[ChatService] LLM 代码生成失败: {type(e).__name__}: {e}")
            logger.error(tb)
            with open("codegen_debug.log", "a", encoding="utf-8") as _dbg:
                _dbg.write(f"EXCEPTION: {type(e).__name__}: {e}\n")
                _dbg.write(tb + "\n")
            return None

    @staticmethod
    def confirm_upload(
        db: Session,
        task_uuid: str,
        project_id: int,
        file_mappings: list[dict],
        user_id: int,
        primer_f: str = "",
        primer_r: str = "",
    ) -> dict:
        """用户上传文件后校验文件类型、压缩文件完整性，然后生成编排脚本"""
        task = ChatService._get_or_create_task(db, None, task_uuid, project_id, user_id)
        logger.info(f"[ChatService] 文件上传确认: task={task.id}, files={len(file_mappings)}")

        # 找到最新的 file_request 消息，获取 required_files 和 tool_ids
        fr_message = (
            Message.where(db, task_id=task.id)
            .filter(Message.type == "file_request")
            .order_by(Message.id.desc())
            .first()
        )
        if not fr_message:
            raise ValueError("No file_request message found")

        required_files_info = json.loads(fr_message.required_files) if fr_message.required_files else []

        # 解析 file_request 的 data 获取 tool_ids
        fr_data = json.loads(fr_message.data) if fr_message.data else {}
        tool_ids = fr_data.get("tool_ids", [])

        # 补充 file_mappings 中的 stored_name（从数据库查 uploaded file 记录）
        enriched_mappings = []
        for fm in file_mappings:
            stored_name = fm.get("stored_name", "")
            if not stored_name:
                file_record = UploadService.find(db, fm["file_id"], user_id)
                if file_record:
                    stored_name = file_record.stored_name
            enriched_mappings.append({
                **fm,
                "stored_name": stored_name or fm.get("original_name", ""),
            })

        # ─── 校验文件扩展名 ───
        errors = []
        for fm in enriched_mappings:
            slot_label = fm["slot_label"]
            original_name = fm["original_name"]
            slot_info = next((rf for rf in required_files_info if rf["label"] == slot_label), None)
            if slot_info and slot_info.get("extensions"):
                allowed = slot_info["extensions"]
                lower_name = original_name.lower()
                if not any(lower_name.endswith(ext.lower()) for ext in allowed):
                    errors.append(f'"{slot_label}" 的文件 {original_name} 格式不正确，允许: {", ".join(allowed)}')

        # ─── 校验压缩文件完整性 ───
        for fm in enriched_mappings:
            file_record = UploadService.find(db, fm["file_id"], user_id)
            if file_record:
                full_path = UploadService.get_file_path(file_record)
                ok, err_msg = UploadService.validate_archive_integrity(full_path, fm["original_name"])
                if not ok:
                    errors.append(f'文件 {fm["original_name"]} 校验失败: {err_msg}')

        if errors:
            return {"success": False, "errors": errors}

        # ─── 生成编排脚本 ───
        candidate_data_str = fr_message.workflow_candidates or "{}"
        try:
            candidate = json.loads(candidate_data_str)
            if not tool_ids:
                tool_chain = candidate.get("tool_chain", [])
                tool_ids = [t["id"] for t in tool_chain if isinstance(t, dict) and "id" in t]
        except (json.JSONDecodeError, TypeError):
            pass

        # 查找 metadata 文件
        metadata_stored = ""
        for fm in enriched_mappings:
            if "metadata" in fm.get("slot_label", "").lower() or "样本信息" in fm.get("slot_label", ""):
                metadata_stored = fm["stored_name"]

        extra_params = {
            "primer_f": primer_f,
            "primer_r": primer_r,
            "metadata_stored": metadata_stored,
        }

        generated_code = ""
        if tool_ids:
            try:
                generated_code = generate_orchestrator_script(
                    tool_ids=tool_ids,
                    file_mappings=enriched_mappings,
                    required_files=required_files_info,
                    extra_params=extra_params,
                    task_id=task.id,
                )
                logger.info(f"[ChatService] 编排脚本生成完成: {len(generated_code)} 字符")
            except Exception as e:
                logger.error(f"[ChatService] 编排脚本生成失败: {e}")
                generated_code = f"# 编排脚本生成失败: {e}\n# tool_ids: {tool_ids}\n"

        # 创建用户消息
        file_names = "、".join(fm["original_name"] for fm in file_mappings)
        user_message = Message(
            task_id=task.id,
            role="user",
            type="text",
            content=f"已上传文件：{file_names}",
            data=json.dumps({"uploaded_files": enriched_mappings}, ensure_ascii=False),
        )
        user_message.save(db)

        # 创建助手消息（校验通过 + 生成的编排脚本）
        assistant_content = (
            "✅ 文件校验完成！\n\n"
            "• 文件格式: 正确\n"
            "• 文件完整性: 通过\n"
            "• 编排脚本: 已生成\n\n"
            "所有文件已就绪，可以开始执行分析任务。"
        )
        assistant_message = Message(
            task_id=task.id,
            role="assistant",
            type="text",
            content=assistant_content,
            data=json.dumps({"upload_validated": True}, ensure_ascii=False),
            result_content=generated_code,
            workflow_candidates=fr_message.workflow_candidates,
        )
        assistant_message.save(db)

        return {
            "success": True,
            "task": task.to_dict(),
            "messages": [user_message.to_dict(), assistant_message.to_dict()],
        }

    @staticmethod
    def start_execution(
        db: Session,
        task_uuid: str,
        project_id: int,
        user_id: int,
    ) -> dict:
        """提交 qsub 任务执行"""
        task = ChatService._get_or_create_task(db, None, task_uuid, project_id, user_id)

        if task.status in ("running", "completed"):
            raise ValueError(f"任务当前状态为 {task.status}，不可重复执行")

        logger.info(f"[ChatService] 开始执行: task={task.id}")

        # 获取 tool_ids（从 select_path 消息）
        select_msg = (
            Message.where(db, task_id=task.id)
            .filter(Message.type == "select_path")
            .order_by(Message.id.desc())
            .first()
        )
        tool_ids = []
        if select_msg and select_msg.data:
            try:
                tool_ids = json.loads(select_msg.data).get("tool_ids", [])
            except (json.JSONDecodeError, TypeError):
                pass

        # 优先从 upload_validated 消息获取生成的代码，兜底从 file_request 消息获取
        validated_message = (
            Message.where(db, task_id=task.id)
            .filter(Message.data.like("%upload_validated%"))
            .order_by(Message.id.desc())
            .first()
        )
        fr_message = (
            Message.where(db, task_id=task.id)
            .filter(Message.type == "file_request")
            .order_by(Message.id.desc())
            .first()
        )
        tid = task.id

        # SGE 脚本头部
        sge_header = f"""#!/bin/bash
#$ -N task_{tid}
#$ -cwd
#$ -j y
#$ -o /shared/task_{tid}.log
export PATH=/opt/conda/bin:$PATH
"""

        # 获取用户上传的文件，构造文件路径映射
        upload_user_msg = (
            Message.where(db, task_id=task.id)
            .filter(Message.role == "user", Message.type == "text", Message.data.like("%uploaded_files%"))
            .order_by(Message.id.desc())
            .first()
        )
        file_env_lines = []
        if upload_user_msg:
            try:
                upload_data = json.loads(upload_user_msg.data) if upload_user_msg.data else {}
                uploaded_files = upload_data.get("uploaded_files", [])
                for fm in uploaded_files:
                    original_name = fm.get("original_name", "")
                    stored_name = fm.get("stored_name", original_name)
                    file_env_lines.append(f'{fm.get("label", original_name).upper().replace(" ", "_")}="/shared/{stored_name}"')
            except (json.JSONDecodeError, AttributeError):
                pass

        # 优先使用生成的真实代码
        generated_code = ""
        if validated_message and validated_message.result_content:
            generated_code = validated_message.result_content
        elif fr_message and fr_message.result_content:
            generated_code = fr_message.result_content

        if generated_code:
            script = sge_header + "\n"
            if file_env_lines:
                script += "# 上传文件路径\n" + "\n".join(file_env_lines) + "\n\n"
            script += generated_code
            logger.info(f"[ChatService] 使用生成的真实代码 (length={len(generated_code)})")
        else:
            script = sge_header + f"""
echo "[$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')] ========== Simulation Job Started =========="
echo "[$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')] Job ID: $JOB_ID"
echo "[$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')] Hostname: $(hostname)"
echo "[$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')] Working directory: $(pwd)"

sleep 5
echo "[$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')] [Step 1/4]  Initializing environment..."

sleep 5
echo "[$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')] [Step 2/4]  Loading input data..."

sleep 5
echo "[$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')] [Step 3/4]  Running analysis..."

sleep 5
echo "[$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')] [Step 4/4]  Writing output files..."

echo "[$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')] ========== Simulation Job Completed =========="
"""
            logger.info(f"[ChatService] 无生成代码，使用模拟脚本")

        container_script = f"/shared/task_{tid}.sh"
        shared_dir = os.getenv("SHARED_DIR", os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "shared")))
        host_script = os.path.join(shared_dir, f"task_{tid}.sh")
        host_script = os.path.normpath(host_script)
        with open(host_script, "w", encoding="utf-8", newline="\n") as f:
            f.write(script)

        # 创建 Execution 记录
        execution = ExecutionService.create(db, tid, tool_ids, script, container_script)

        # 检查 SGE 执行节点是否就绪
        ChatService._ensure_sge_execd()

        # 通过 docker exec 执行 qsub
        qsub_cmd = f"source /opt/sge/default/common/settings.sh && qsub -o /shared {container_script}"
        logger.info(f"[ChatService] 执行命令: {qsub_cmd}")

        result = subprocess.run(
            ["docker", "exec", "sge-master", "bash", "-c", qsub_cmd],
            capture_output=True, text=True, timeout=30,
        )
        output = result.stdout.strip()
        logger.info(f"[ChatService] qsub 输出: {output}")

        if result.returncode != 0:
            error_msg = result.stderr.strip() or output
            ExecutionService.fail(db, execution.id, f"qsub 提交失败: {error_msg}")
            raise ValueError(f"qsub 提交失败: {error_msg}")

        # 解析 job ID
        match = re.search(r"Your job (\d+)", output)
        if not match:
            ExecutionService.fail(db, execution.id, f"无法解析 qsub 返回: {output}")
            raise ValueError(f"无法解析 qsub 返回: {output}")

        qsub_id = match.group(1)
        logger.info(f"[ChatService] 任务已提交, qsub_id={qsub_id}")

        ExecutionService.start(db, execution.id, qsub_id)

        # 创建助手消息
        ai_message = Message(
            task_id=task.id,
            role="assistant",
            type="text",
            content=f"任务已提交，Job ID: {qsub_id}\n\n正在执行分析脚本，请等待日志输出...",
            data=json.dumps({"execution_logs": True, "qsub_id": qsub_id, "execution_id": execution.id}, ensure_ascii=False),
        )
        ai_message.save(db)

        return {
            "task": task.to_dict(),
            "message": ai_message.to_dict(),
            "execution": execution.to_dict(),
            "qsub_id": qsub_id,
        }

    @staticmethod
    def simulate_execution(
        db: Session,
        task_uuid: str,
        project_id: int,
        user_id: int,
    ) -> dict:
        """模拟执行任务：只包含已选路径的 steps，每步用 5-10s sleep 模拟，通过真实 SGE 提交。"""
        task = ChatService._get_or_create_task(db, None, task_uuid, project_id, user_id)

        if task.status in ("running", "completed"):
            raise ValueError(f"任务当前状态为 {task.status}，不可重复执行")

        logger.info(f"[ChatService] 开始模拟执行: task={task.id}")

        # 获取 tool_ids（从 select_path 消息）
        select_msg = (
            Message.where(db, task_id=task.id)
            .filter(Message.type == "select_path")
            .order_by(Message.id.desc())
            .first()
        )
        tool_ids = []
        if select_msg and select_msg.data:
            try:
                tool_ids = json.loads(select_msg.data).get("tool_ids", [])
            except (json.JSONDecodeError, TypeError):
                pass

        if not tool_ids:
            raise ValueError("未找到已选路径，无法模拟执行")

        tid = task.id

        # 工具 ID -> 中文名映射
        from pkg.amplicon.amplicon_tools import get_all_tools
        tool_name_map = {t.id: t.name for t in get_all_tools()}

        # SGE 脚本头部
        sge_header = f"""#!/bin/bash
#$ -N task_{tid}
#$ -cwd
#$ -j y
#$ -o /shared/task_{tid}.log
export PATH=/opt/conda/bin:$PATH
"""

        # 构造模拟 steps：每个 step 随机 5-10s sleep，前后带时间戳日志
        step_lines = []
        total = len(tool_ids)
        for idx, tool_id in enumerate(tool_ids, start=1):
            name = tool_name_map.get(tool_id, tool_id)
            sleep_seconds = random.randint(5, 10)
            step_lines.append(
                f'echo "[$(TZ=\'Asia/Shanghai\' date \'+%Y-%m-%d %H:%M:%S\')] Step {idx}/{total}: {name} ({tool_id}) 开始..."'
            )
            step_lines.append(f"sleep {sleep_seconds}")
            step_lines.append(
                f'echo "[$(TZ=\'Asia/Shanghai\' date \'+%Y-%m-%d %H:%M:%S\')] Step {idx}/{total}: {name} ({tool_id}) 完成"'
            )
            step_lines.append("")

        script = sge_header + "\n" + "\n".join(step_lines)
        script += '\necho "[$(TZ=\'Asia/Shanghai\' date \'+%Y-%m-%d %H:%M:%S\')] 模拟执行全部完成"\n'
        script += 'echo "Job Completed"\n'

        logger.info(f"[ChatService] 生成模拟脚本: task={task.id}, steps={total}")

        container_script = f"/shared/task_{tid}.sh"
        shared_dir = os.getenv("SHARED_DIR", os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "shared")))
        host_script = os.path.join(shared_dir, f"task_{tid}.sh")
        host_script = os.path.normpath(host_script)
        with open(host_script, "w", encoding="utf-8", newline="\n") as f:
            f.write(script)

        # 创建 Execution 记录
        execution = ExecutionService.create(db, tid, tool_ids, script, container_script)

        # 检查 SGE 执行节点是否就绪
        ChatService._ensure_sge_execd()

        # 通过 docker exec 执行 qsub（与真实执行一致）
        qsub_cmd = f"source /opt/sge/default/common/settings.sh && qsub -o /shared {container_script}"
        logger.info(f"[ChatService] 模拟执行提交命令: {qsub_cmd}")

        result = subprocess.run(
            ["docker", "exec", "sge-master", "bash", "-c", qsub_cmd],
            capture_output=True, text=True, timeout=30,
        )
        output = result.stdout.strip()
        logger.info(f"[ChatService] qsub 输出: {output}")

        if result.returncode != 0:
            error_msg = result.stderr.strip() or output
            ExecutionService.fail(db, execution.id, f"qsub 提交失败: {error_msg}")
            raise ValueError(f"qsub 提交失败: {error_msg}")

        # 解析 job ID
        match = re.search(r"Your job (\d+)", output)
        if not match:
            ExecutionService.fail(db, execution.id, f"无法解析 qsub 返回: {output}")
            raise ValueError(f"无法解析 qsub 返回: {output}")

        qsub_id = match.group(1)
        logger.info(f"[ChatService] 模拟任务已提交, qsub_id={qsub_id}")

        ExecutionService.start(db, execution.id, qsub_id)

        # 创建助手消息
        ai_message = Message(
            task_id=task.id,
            role="assistant",
            type="text",
            content=f"任务已提交（模拟执行），Job ID: {qsub_id}\n\n正在模拟分析脚本（共 {total} 步），请等待日志输出...",
            data=json.dumps({"execution_logs": True, "qsub_id": qsub_id, "execution_id": execution.id}, ensure_ascii=False),
        )
        ai_message.save(db)

        return {
            "task": task.to_dict(),
            "message": ai_message.to_dict(),
            "execution": execution.to_dict(),
            "qsub_id": qsub_id,
        }

    @staticmethod
    def get_execution_logs(
        db: Session,
        task_uuid: str,
        user_id: int,
    ) -> dict:
        """获取任务执行日志"""
        task = Task.where(db, uuid=task_uuid).first()
        if not task or task.user_id != user_id:
            raise ValueError("Task not found")

        execution = ExecutionService.get_latest(db, task.id)
        if not execution or not execution.qsub_id:
            return {"logs": "", "completed": False, "qsub_id": "", "status": task.status}

        # SGE 日志文件: task_{id}.o{qsub_id}
        log_filename = f"task_{task.id}.o{execution.qsub_id}"
        shared_dir = os.getenv("SHARED_DIR", os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "shared")))
        host_log = os.path.join(shared_dir, log_filename)
        host_log = os.path.normpath(host_log)
        logs = ""
        completed = False

        if os.path.exists(host_log):
            try:
                with open(host_log, "r", encoding="utf-8", errors="replace") as f:
                    logs = f.read()
                if "Job Completed" in logs and execution.status == "running":
                    completed = True
                    ExecutionService.complete(db, execution.id, logs)

                    # 更新执行消息的 data
                    exec_msg = (
                        Message.where(db, task_id=task.id)
                        .filter(Message.type == "text")
                        .order_by(Message.id.desc())
                        .first()
                    )
                    if exec_msg and exec_msg.data:
                        try:
                            data = json.loads(exec_msg.data)
                            if data.get("execution_logs") and not data.get("execution_completed"):
                                data["execution_completed"] = True
                                data["execution_log_content"] = logs
                                exec_msg.data = json.dumps(data, ensure_ascii=False)
                                exec_msg.save(db)
                        except (json.JSONDecodeError, TypeError):
                            pass
                elif execution.status in ("completed", "failed"):
                    completed = execution.status == "completed"
            except Exception as e:
                logger.warning(f"[ChatService] 读取日志失败: {e}")
                logs = f"读取日志失败: {e}"

        return {
            "logs": logs,
            "completed": completed,
            "qsub_id": execution.qsub_id,
            "status": task.status,
            "execution": execution.to_dict(),
        }

    @staticmethod
    def download_execution_logs(
        db: Session,
        task_uuid: str,
        user_id: int,
    ) -> tuple[str, str]:
        """返回任务执行日志文件路径和下载文件名"""
        task = Task.where(db, uuid=task_uuid).first()
        if not task or task.user_id != user_id:
            raise ValueError("Task not found")

        execution = ExecutionService.get_latest(db, task.id)
        if not execution or not execution.qsub_id:
            raise ValueError("没有执行记录")

        log_filename = f"task_{task.id}.o{execution.qsub_id}"
        shared_dir = os.getenv("SHARED_DIR", os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "shared")))
        host_log = os.path.join(shared_dir, log_filename)
        host_log = os.path.normpath(host_log)

        if not os.path.exists(host_log):
            raise ValueError("日志文件不存在")

        download_name = f"task_{task.id}_{execution.qsub_id}.log"
        return host_log, download_name

    @staticmethod
    def retry_execution(
        db: Session,
        task_uuid: str,
        project_id: int,
        user_id: int,
    ) -> dict:
        """一键重试：复用上次执行的脚本重新提交"""
        task = ChatService._get_or_create_task(db, None, task_uuid, project_id, user_id)

        if task.status not in ("failed", "cancelled"):
            raise ValueError(f"任务当前状态为 {task.status}，不可重试")

        last_execution = ExecutionService.get_latest(db, task.id)
        if not last_execution:
            raise ValueError("没有找到执行记录")

        tool_ids = []
        try:
            tool_ids = json.loads(last_execution.tool_ids) if last_execution.tool_ids else []
        except (json.JSONDecodeError, TypeError):
            pass

        tid = task.id
        script = last_execution.script_content
        container_script = last_execution.script_path

        shared_dir = os.getenv("SHARED_DIR", os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "shared")))
        host_script = os.path.join(shared_dir, f"task_{tid}.sh")
        host_script = os.path.normpath(host_script)
        with open(host_script, "w", encoding="utf-8", newline="\n") as f:
            f.write(script)

        execution = ExecutionService.create(db, tid, tool_ids, script, container_script)

        # 检查 SGE 执行节点是否就绪
        ChatService._ensure_sge_execd()

        qsub_cmd = f"source /opt/sge/default/common/settings.sh && qsub -o /shared {container_script}"
        logger.info(f"[ChatService] 重试执行: {qsub_cmd}")

        result = subprocess.run(
            ["docker", "exec", "sge-master", "bash", "-c", qsub_cmd],
            capture_output=True, text=True, timeout=30,
        )
        output = result.stdout.strip()

        if result.returncode != 0:
            error_msg = result.stderr.strip() or output
            ExecutionService.fail(db, execution.id, f"qsub 提交失败: {error_msg}")
            raise ValueError(f"qsub 提交失败: {error_msg}")

        match = re.search(r"Your job (\d+)", output)
        if not match:
            ExecutionService.fail(db, execution.id, f"无法解析 qsub 返回: {output}")
            raise ValueError(f"无法解析 qsub 返回: {output}")

        qsub_id = match.group(1)
        ExecutionService.start(db, execution.id, qsub_id)

        ai_message = Message(
            task_id=task.id,
            role="assistant",
            type="text",
            content=f"任务已重新提交，Job ID: {qsub_id}\n\n正在执行分析脚本，请等待日志输出...",
            data=json.dumps({"execution_logs": True, "qsub_id": qsub_id, "execution_id": execution.id, "retry": True}, ensure_ascii=False),
        )
        ai_message.save(db)

        return {
            "task": task.to_dict(),
            "message": ai_message.to_dict(),
            "execution": execution.to_dict(),
            "qsub_id": qsub_id,
        }

    @staticmethod
    def reupload_and_execute(
        db: Session,
        task_uuid: str,
        project_id: int,
        file_mappings: list[dict],
        user_id: int,
        primer_f: str = "",
        primer_r: str = "",
    ) -> dict:
        """重新上传文件并重新执行"""
        task = ChatService._get_or_create_task(db, None, task_uuid, project_id, user_id)

        if task.status not in ("failed", "cancelled"):
            raise ValueError(f"任务当前状态为 {task.status}，不可重新上传执行")

        # 复用 confirm_upload 的校验和脚本生成逻辑
        result = ChatService.confirm_upload(db, task_uuid, project_id, file_mappings, user_id, primer_f, primer_r)
        if not result.get("success", True):
            return result

        # 然后直接执行
        return ChatService.start_execution(db, task_uuid, project_id, user_id)
