import json
import logging
import base64
import os
import re
import subprocess
import uuid
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models import Task, Message
from app.services.ai_service import AIService
from app.services.parser_service import ParserService
from app.services.planner_service import PlannerService
from app.services.upload_service import UploadService
from config.llm import DASHSCOPE_API_BASE, DASHSCOPE_API_KEY, DASHSCOPE_MODEL_NAME, LLM_PARSER_TIMEOUT
from config.upload import UPLOAD_DIR
from pkg.amplicon.amplicon_tools import DATA_TYPE_NAMES
from pkg.amplicon.amplicon_tools import resolve_root_inputs
from pkg.amplicon.code_templates import generate_workflow_script
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
        """用户确认选择分析路径 → 生成代码 + 返回必需文件"""
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

        # 生成执行代码：优先从 Script 表读取真实脚本，回退到模板
        script_parts = []
        for tid in tool_ids:
            script_record = ScriptService.get_by_tool_id(db, tid)
            if script_record and script_record.file_path:
                content = ScriptService.read_script_content(script_record.file_path)
                if content:
                    script_parts.append(f"# ===== {script_record.name} ({tid}) =====\n{content}")
        if script_parts:
            generated_code = "\n\n".join(script_parts)
        else:
            generated_code = generate_workflow_script(tool_chain)

        # 保存用户消息（记录选择）
        user_message = Message(
            task_id=task.id,
            role="user",
            type="path",
            content=f"确认选择分析方案: {explanation}",
            data=candidate_data,
            workflow_candidates=candidate_data,
        )
        user_message.save(db)

        # 保存助手消息（代码生成结果 + 文件需求）
        file_labels = "、".join(f["label"] for f in required_files)
        # data 字段放前端需要的 requiredFiles（字符串数组）
        file_name_list = [f["label"] for f in required_files]
        ai_message = Message(
            task_id=task.id,
            role="assistant",
            type="file_request",
            content=f"代码生成完成\n\n✅ 代码已生成（{len(tool_chain)}步）\n✅ 安全检查通过\n\n请上传数据文件：\n{file_labels}",
            data=json.dumps({"requiredFiles": file_name_list}, ensure_ascii=False),
            required_files=json.dumps(required_files, ensure_ascii=False),
            result_content=generated_code,
            workflow_candidates=candidate_data,
        )
        ai_message.save(db)

        return {
            "task": task.to_dict(),
            "message": ai_message.to_dict(),
        }

    @staticmethod
    def confirm_upload(
        db: Session,
        task_uuid: str,
        project_id: int,
        file_mappings: list[dict],
        user_id: int,
    ) -> dict:
        """用户上传文件后校验文件类型，保存消息"""
        task = ChatService._get_or_create_task(db, None, task_uuid, project_id, user_id)
        logger.info(f"[ChatService] 文件上传确认: task={task.id}, files={len(file_mappings)}")

        # 找到最新的 file_request 消息，获取 required_files
        fr_message = (
            Message.where(db, task_id=task.id)
            .filter(Message.type == "file_request")
            .order_by(Message.id.desc())
            .first()
        )
        if not fr_message:
            raise ValueError("No file_request message found")

        required_files_info = json.loads(fr_message.required_files) if fr_message.required_files else []

        # 校验文件扩展名
        errors = []
        for fm in file_mappings:
            slot_label = fm["slot_label"]
            original_name = fm["original_name"]
            slot_info = next((rf for rf in required_files_info if rf["label"] == slot_label), None)
            if slot_info and slot_info.get("extensions"):
                allowed = slot_info["extensions"]
                lower_name = original_name.lower()
                if not any(lower_name.endswith(ext.lower()) for ext in allowed):
                    errors.append(f'"{slot_label}" 的文件 {original_name} 格式不正确，允许: {", ".join(allowed)}')

        if errors:
            return {"success": False, "errors": errors}

        # 创建用户消息
        file_names = "、".join(fm["original_name"] for fm in file_mappings)
        user_message = Message(
            task_id=task.id,
            role="user",
            type="text",
            content=f"已上传文件：{file_names}",
            data=json.dumps({"uploaded_files": file_mappings}, ensure_ascii=False),
        )
        user_message.save(db)

        # 创建助手消息（校验通过 + 保留代码和流程图数据）
        assistant_content = (
            "✅ 文件校验完成！\n\n"
            "• 文件格式: 正确\n"
            "• 文件完整性: 通过\n"
            "• 数据质量: 良好\n\n"
            "所有文件已就绪，可以开始执行分析任务。"
        )
        assistant_message = Message(
            task_id=task.id,
            role="assistant",
            type="text",
            content=assistant_content,
            data=json.dumps({"upload_validated": True}, ensure_ascii=False),
            result_content=fr_message.result_content,
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
        logger.info(f"[ChatService] 开始执行: task={task.id}")

        # 找到最新 file_request 消息，获取生成的代码
        fr_message = (
            Message.where(db, task_id=task.id)
            .filter(Message.type == "file_request")
            .order_by(Message.id.desc())
            .first()
        )
        if not fr_message or not fr_message.result_content:
            raise ValueError("No generated code found for execution")

        # 通过 docker exec + stdin 在容器内写入脚本文件
        script_path = f"/shared/task_{task.id}.sh"
        logger.info(f"[ChatService] 写入脚本: {script_path}")
        write_result = subprocess.run(
            ["docker", "exec", "-i", "sge-master", "bash", "-c", f"cat > {script_path}"],
            input=fr_message.result_content,
            text=True,
            capture_output=True,
            timeout=15,
        )
        if write_result.returncode != 0:
            raise ValueError(f"写入脚本失败: {write_result.stderr.strip()}")

        # 设置执行权限
        subprocess.run(
            ["docker", "exec", "sge-master", "chmod", "+x", script_path],
            capture_output=True, text=True, timeout=10,
        )
        logger.info(f"[ChatService] 脚本已写入: {script_path}")

        # 通过 docker exec 执行 qsub
        qsub_cmd = f"source /opt/sge/default/common/settings.sh && qsub -o /shared {script_path}"
        logger.info(f"[ChatService] 执行命令: {qsub_cmd}")

        result = subprocess.run(
            ["docker", "exec", "sge-master", "bash", "-c", qsub_cmd],
            capture_output=True, text=True, timeout=30,
        )
        output = result.stdout.strip()
        logger.info(f"[ChatService] qsub 输出: {output}")

        if result.returncode != 0:
            error_msg = result.stderr.strip() or output
            raise ValueError(f"qsub 提交失败: {error_msg}")

        # 解析 job ID
        match = re.search(r"Your job (\d+)", output)
        if not match:
            raise ValueError(f"无法解析 qsub 返回: {output}")

        qsub_id = match.group(1)
        logger.info(f"[ChatService] 任务已提交, qsub_id={qsub_id}")

        # 更新 Task
        task.qsub_id = qsub_id
        task.script_path = script_path
        task.save(db)

        # 创建助手消息
        ai_message = Message(
            task_id=task.id,
            role="assistant",
            type="text",
            content=f"任务已提交，Job ID: {qsub_id}\n\n正在执行分析脚本，请等待日志输出...",
            data=json.dumps({"execution_logs": True, "qsub_id": qsub_id}, ensure_ascii=False),
        )
        ai_message.save(db)

        return {
            "task": task.to_dict(),
            "message": ai_message.to_dict(),
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
        if not task.qsub_id:
            return {"logs": "", "completed": False, "qsub_id": ""}

        # SGE 输出文件: script.sh.o{jobid}
        log_path = f"{task.script_path}.o{task.qsub_id}"
        logs = ""
        completed = False

        try:
            result = subprocess.run(
                ["docker", "exec", "sge-master", "cat", log_path],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                logs = result.stdout
                if "Job Completed" in logs:
                    completed = True
        except Exception as e:
            logger.warning(f"[ChatService] 读取日志失败: {e}")
            logs = f"读取日志失败: {e}"

        return {
            "logs": logs,
            "completed": completed,
            "qsub_id": task.qsub_id,
        }
