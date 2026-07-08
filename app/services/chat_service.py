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
from app.services.domain_service import DomainService
from app.services.domain_classifier import DomainClassifier
from app.services.upload_service import UploadService
from app.services.intent_agent import IntentAgent
from app.services.tool_genesis_service import ToolGenesisService
from app.services.analysis_router import AnalysisRouter
from app.services.standalone_analysis_agent import StandaloneAnalysisAgent
from app.services.standalone_script_service import StandaloneScriptService
from config.llm import DASHSCOPE_API_BASE, DASHSCOPE_API_KEY, DASHSCOPE_MODEL_NAME, LLM_CODEGEN_TIMEOUT, LLM_PARSER_TIMEOUT
from config.upload import UPLOAD_DIR
from pkg.amplicon.amplicon_tools import DATA_TYPE_NAMES
from pkg.amplicon.code_templates import generate_workflow_script
from pkg.amplicon.orchestrator import (
    generate_orchestrator_script,
    build_sample_mapping_block,
    build_derived_files_block,
    _resolve_fastq_pair_uploads,
)
from app.services.script_service import ScriptService

logger = logging.getLogger(__name__)

# 用户改的参数值会原样拼进 qsub 脚本，只允许字母/数字/._/-（无空格、无 shell 元字符）
_PARAM_OVERRIDE_RE = re.compile(r"^[A-Za-z0-9._/\-]+$")


def _sanitize_param_overrides(tool_chain) -> dict:
    """从候选 tool_chain 提取并校验用户改的 param_overrides。

    只保留字符集安全的值；挡掉空、超长(>64)或含 shell 元字符/空格的值（防注入），
    非法值丢弃并记 warning。返回 {tool_id: {flag: value}}。
    """
    out: dict[str, dict[str, str]] = {}
    if not isinstance(tool_chain, list):
        return out
    for t in tool_chain:
        if not isinstance(t, dict) or not t.get("id"):
            continue
        raw = t.get("param_overrides")
        if not isinstance(raw, dict) or not raw:
            continue
        clean: dict[str, str] = {}
        for flag, val in raw.items():
            sval = "" if val is None else str(val).strip()
            if not sval or len(sval) > 64 or not _PARAM_OVERRIDE_RE.match(sval):
                logger.warning(f"[ChatService] 丢弃非法 param_override {flag}={sval!r}")
                continue
            clean[flag] = sval
        if clean:
            out[t["id"]] = clean
    return out


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
    def _route_decision(db: Session, domain_id: int, intent: dict, content: str, history_dicts: list[dict]) -> dict:
        """根据意图代理结果决定回复。

        - sufficient=false → 把 questions 组合成一条多问题追问消息（一次问全）；
          代理没给问题则走通用澄清。
        - sufficient=true → 用 available/goal 规划；规划空→通用兜底（Phase 2 会改成能力缺口提议）。
        """
        sufficient = bool(intent.get("sufficient", False))
        questions = intent.get("questions") or []
        available = intent.get("available_inputs") or []
        goals = intent.get("goal_types") or []

        # 不够 → 一次问全
        if not sufficient:
            if questions:
                body = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions))
                text = f"为了帮你定准分析流程，先一次性确认几件事：\n{body}"
            else:
                text = ParserService.generate_clarification(content, history_dicts)
            return {
                "type": "clarification",
                "content": text,
                "data": "",
                "goal_types": json.dumps(goals, ensure_ascii=False),
            }

        # 够 → 规划
        candidates = PlannerService.plan_workflow(db, domain_id, available, goals)

        if not candidates:
            gap = IntentAgent.classify_capability_gap(db, domain_id, available, goals, content)
            if gap.get("plausible"):
                input_names = ChatService._format_data_type_names(available)
                goal_names = ChatService._format_data_type_names(goals)
                missing = gap.get("missing_link") or "该环节"
                return {
                    "type": "clarification",
                    "content": (
                        f"根据你的数据（{input_names}）和目标（{goal_names}），平台目前没有现成流程"
                        f"覆盖这条链（缺：{missing}）。\n"
                        "不过我可以临时生成一个单步脚本来补上这个缺口，生成后就能接上既有流程继续。"
                        "要我现在生成吗？"
                    ),
                    "data": json.dumps({"capability_gap": True, "missing_link": missing}, ensure_ascii=False),
                    "available_inputs": json.dumps(available, ensure_ascii=False),
                    "goal_types": json.dumps(goals, ensure_ascii=False),
                }
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
    def _default_intent_route(
        db: Session, domain, domain_id: int, content: str, history_dicts: list[dict],
        task: Task, user_message: Message, history: list,
    ) -> dict:
        """默认路径：IntentAgent 理解意图 → _route_decision 路由。失败回退通用 AI。"""
        try:
            intent = IntentAgent.understand(db, domain, content, history_dicts)
            logger.info(
                f"[ChatService] 意图代理结果: sufficient={intent.get('sufficient')} "
                f"fallback={intent.get('fallback')}"
            )
            return ChatService._route_decision(db, domain_id, intent, content, history_dicts)
        except Exception as e:
            logger.error(f"[ChatService] 意图识别/规划异常，回退到通用 AI: {e}")
            return AIService.generate_response(task.id, user_message, history)

    # ─── Path B：独立单步分析闭环（见 STANDALONE_ANALYSIS_PLAN.md）──────────
    @staticmethod
    def _standalone_route(
        db: Session, content: str, history_dicts: list[dict],
        task: Task, user_id: int, verdict: dict, form: dict,
    ) -> dict:
        """Path B 入口：合理生信 + 单步独立分析 → 召回模板 / 理解 → 清单或追问。

        ① 先召回（§4.6 retrieve-then-judge）：高置信同义命中已归档模板 → 原样重放清单（复用脚本）。
        ② 未命中 → StandaloneAnalysisAgent.understand 从头理解：
           - sufficient   → markdown 数据清单 + file_request（触发既有上传面板），完整契约存入 data 供 P3 生成 / P4 执行。
           - 不足         → clarification 编号追问（一次问全，像专家对待小白）。
        """
        # ① 召回
        tmpl = StandaloneScriptService.recall_template(db, content)
        if tmpl and tmpl.get("data_requirements"):
            logger.info(f"[ChatService] Path B 命中模板 {tmpl.get('tool_id')}，重放清单")
            return ChatService._build_standalone_checklist(
                tmpl.get("analysis_type") or form.get("analysis_type") or "独立分析",
                tmpl.get("data_requirements") or [],
                tmpl.get("params") or [],
                runtime_hint=tmpl.get("runtime_hint", ""),
                reused=True,
                tool_id=tmpl.get("tool_id"),
            )

        # ② 未命中 → 先征得用户同意再生成（避免静默几十秒跑生成，UX 差）。
        #    同意 → 下一轮 _handle_standalone_generate 现场生成；不同意/改主意 → 正常分流。
        #    理解与生成都不在这一步，故本步很快（仅召回 + 一次廉价形态判定，都已在上游完成）。
        analysis_type = form.get("analysis_type") or "独立分析"
        logger.info(f"[ChatService] Path B 未命中模板，征求生成同意: {analysis_type}")
        return {
            "type": "clarification",
            "content": (
                f"这个分析（**{analysis_type}**）我还没有现成的脚本模板。\n"
                f"我可以现在帮你现场生成一个自包含脚本（大概几十秒）。要生成吗？\n"
                f"（回复「好」「生成」即可；想换个分析或先聊聊就说）"
            ),
            "data": json.dumps({
                "standalone": True,
                "standalone_codegen_offer": True,
                "analysis_type": analysis_type,
                "user_query": content,
            }, ensure_ascii=False),
        }

    @staticmethod
    def _pending_standalone_offer(history: list) -> dict | None:
        """看上一条 assistant 消息是否 Path B 的『要现在生成吗』提议。

        返回 {analysis_type, user_query} 或 None。仅识别紧邻的提议（offer 之后若系统已回过
        别的消息则不再触发）——同 _pending_codegen_offer 的紧邻语义。
        """
        for msg in reversed(history):
            if msg.role != "assistant":
                continue
            if not msg.data:
                return None
            try:
                data = json.loads(msg.data)
            except (json.JSONDecodeError, TypeError):
                return None
            if not data.get("standalone_codegen_offer"):
                return None
            return {
                "analysis_type": data.get("analysis_type", ""),
                "user_query": data.get("user_query", ""),
            }
        return None

    @staticmethod
    def _handle_standalone_generate(
        db: Session, offer: dict, content: str, task: Task, user_id: int,
    ) -> dict:
        """用户同意现生成 → 理解(原查询) → 生成自包含脚本 + 归档 → 清单(file_request)。

        理解针对【提议时记下的原查询】（不是「好/生成吧」这句），故能拿到精确列名/参数。
        生成失败/理解不足 → 友好提示，不崩、不伪造。
        """
        user_query = (offer.get("user_query") or "").strip() or content
        analysis_type = offer.get("analysis_type") or "独立分析"

        result = StandaloneAnalysisAgent.understand(user_query, None)
        at = result.get("analysis_type") or analysis_type

        if not result.get("sufficient"):
            questions = result.get("questions") or []
            if questions:
                body = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions))
                text = f"生成前先一次性确认几件事：\n{body}"
            else:
                text = "要生成这个分析，我还需要了解你的数据（格式/关键列）和目标，请补充。"
            logger.info(f"[ChatService] Path B 同意生成但信息不足，追问 {len(questions)} 问")
            return {
                "type": "clarification",
                "content": text,
                "data": json.dumps({"standalone": True, "analysis_type": at}, ensure_ascii=False),
            }

        archived = None
        try:
            archived = StandaloneScriptService.generate_and_archive(
                at,
                result.get("data_requirements") or [],
                result.get("params") or [],
                result.get("runtime_hint", ""),
                user_query, db, user_id,
            )
        except Exception as e:
            logger.warning(f"[ChatService] Path B 生成/归档失败: {type(e).__name__}: {e}")

        if not archived:
            return {
                "type": "clarification",
                "content": "抱歉，脚本这次没生成成功，换个说法再试一次？",
                "data": json.dumps({"standalone": True, "analysis_type": at}, ensure_ascii=False),
            }

        tool_id = archived.get("tool_id")
        logger.info(f"[ChatService] Path B 已生成归档: {tool_id}")
        resp = ChatService._build_standalone_checklist(
            at,
            result.get("data_requirements") or [],
            result.get("params") or [],
            runtime_hint=result.get("runtime_hint", ""),
            reused=False,
            tool_id=tool_id,
        )
        # 前置「已生成」提示（前端对 file_request 的 ✅ 行有专门渲染）
        resp["content"] = f"✅ 脚本已生成并归档（{tool_id}）。\n\n" + resp["content"]
        return resp

    @staticmethod
    def _build_standalone_checklist(
        analysis_type: str, data_requirements: list[dict], params: list[dict],
        runtime_hint: str = "", reused: bool = False, tool_id: int | None = None,
    ) -> dict:
        """把 data_requirements/params 渲染成 markdown 清单 + file_request（触发既有上传面板）。

        返回 type=file_request 消息体：
        - content = 清单 markdown（必需/可选 tag、列名、格式、参数默认），前端按既有规则渲染文本；
        - data    = {requiredFiles(供上传面板 slot), standalone, analysis_type, data_requirements,
                     params, runtime_hint, reused, tool_id}（完整契约，供 P3 生成 / P4 执行读取）；
        - required_files = slot 列表（{label,extensions,required,...}，供 confirm_upload 按 label 校验扩展名）。
        """
        req_items = [d for d in data_requirements if d.get("required")]
        opt_items = [d for d in data_requirements if not d.get("required")]

        lines: list[str] = []
        if reused:
            lines.append(f"💡 我之前生成过【{analysis_type}】的模板，直接复用。")
        lines.append(f"### 📋 {analysis_type} —— 请准备以下数据")

        def _fmt_item(d: dict, tag: str) -> None:
            lines.append(f"- **{d.get('label', '')}** 〔{tag}〕")
            sub: list[str] = []
            fmt = d.get("format", "")
            if fmt:
                sub.append(f"格式 {fmt}")
            cols = d.get("columns") or []
            if cols:
                sub.append("列：" + " / ".join(cols))
            if sub:
                lines.append("  - " + "；".join(sub))
            desc = d.get("columns_desc", "")
            if desc:
                lines.append(f"  - {desc}")

        for d in req_items:
            _fmt_item(d, "必需")
        for d in opt_items:
            _fmt_item(d, "可选")

        if params:
            lines.append("")
            lines.append("**可选参数**（未指定用默认值）：")
            for p in params:
                opts = p.get("options") or []
                tail = f"（可选：{' / '.join(opts)}）" if opts else ""
                lines.append(f"- {p.get('label', '')}：默认「{p.get('default', '')}」{tail}")

        lines.append("")
        lines.append("准备好后请上传上述〔必需〕文件。")
        content = "\n".join(lines)

        # 上传面板 slot：label 作为 confirm_upload 的 slot_label 锚点
        required_files = [
            {
                "typeId": d.get("key", "") or d.get("label", ""),
                "label": d.get("label", ""),
                "description": d.get("columns_desc", ""),
                "extensions": ChatService._fmt_extensions(d.get("format", "")),
                "required": bool(d.get("required", False)),
                "multiple": bool(d.get("multiple", False)),
            }
            for d in data_requirements
        ]
        labels = [d.get("label", "") for d in data_requirements]

        data = {
            "requiredFiles": labels,
            "standalone": True,
            "analysis_type": analysis_type,
            "data_requirements": data_requirements,
            "params": params,
            "runtime_hint": runtime_hint,
            "reused": reused,
            "tool_id": tool_id,
        }
        return {
            "type": "file_request",
            "content": content,
            "data": json.dumps(data, ensure_ascii=False),
            "required_files": json.dumps(required_files, ensure_ascii=False),
        }

    @staticmethod
    def _fmt_extensions(fmt: str) -> list[str]:
        """格式串 → 扩展名白名单。TSV→[.tsv]；CSV→[.csv]；TSV/CSV→两者；未知→表格式兜底。"""
        fmt = (fmt or "").upper()
        exts: list[str] = []
        for token in ("TSV", "CSV", "TXT"):
            if token in fmt:
                exts.append("." + token.lower())
        return exts or [".tsv", ".csv", ".txt"]

    @staticmethod
    def _pending_codegen_offer(history: list) -> dict | None:
        """看上一条 assistant 消息是否能力缺口提议（Phase 2 发出）。

        返回 {available, goals, missing_link} 或 None。仅识别【紧邻】的提议——
        若 offer 之后系统已回过别的消息则不再触发。
        """
        for msg in reversed(history):
            if msg.role != "assistant":
                continue
            if not msg.data:
                return None
            try:
                data = json.loads(msg.data)
            except (json.JSONDecodeError, TypeError):
                return None
            if not data.get("capability_gap"):
                return None
            available = json.loads(msg.available_inputs) if msg.available_inputs else []
            goals = json.loads(msg.goal_types) if msg.goal_types else []
            return {
                "available": available,
                "goals": goals,
                "missing_link": data.get("missing_link", ""),
            }
        return None

    @staticmethod
    def _judge_codegen_acceptance(content: str) -> str:
        """判定用户对『要我现在生成吗？』的回复：accept / decline / other。

        LLM 判定；不可用/失败走关键词兜底。
        """
        text = (content or "").strip()
        if not text:
            return "other"
        if not DASHSCOPE_API_KEY:
            return ChatService._acceptance_keyword_fallback(text)
        system = (
            "我刚向用户提议『现在生成一个补缺口的单步脚本』。请判定用户这句回复的意图，"
            "只输出 JSON：{\"verdict\": \"accept|decline|other\"}。\n"
            "- accept：明确同意生成（好/可以/行/要/生成吧/同意/yes）；\n"
            "- decline：明确拒绝（不用/算了/不要/别/换一个）；\n"
            "- other：既非同意也非拒绝——补充新信息、改需求、提问、跑题"
            "（如 我有双端数据 / 什么是单端 / 帮我做别的）。"
        )
        try:
            resp = httpx.post(
                f"{DASHSCOPE_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
                json={
                    "model": DASHSCOPE_MODEL_NAME,
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": text},
                    ],
                },
                timeout=LLM_PARSER_TIMEOUT,
            )
            resp.raise_for_status()
            verdict = str(
                json.loads(resp.json()["choices"][0]["message"]["content"]).get("verdict", "")
            ).strip().lower()
            if verdict in ("accept", "decline", "other"):
                return verdict
            return ChatService._acceptance_keyword_fallback(text)
        except Exception as e:
            logger.warning(f"[ChatService] 同意判定 LLM 失败，走关键词: {type(e).__name__}: {e}")
            return ChatService._acceptance_keyword_fallback(text)

    @staticmethod
    def _acceptance_keyword_fallback(text: str) -> str:
        """关键词兜底：decline 优先于 accept（避免『不好』误判）。"""
        t = text.lower()
        # decline 用更具体的词（单字『不』会误伤『不错』）
        for w in ("不用", "不要", "算了", "别生", "拒绝", "换", "否", "no", "cancel"):
            if w in t:
                return "decline"
        for w in ("好", "可以", "行", "要", "同意", "生成", "是的", "对", "嗯", "ok", "yes", "来吧"):
            if w in t:
                return "accept"
        return "other"

    @staticmethod
    def _handle_codegen_accept(
        db: Session, domain_id: int, offer: dict, content: str, user_id: int,
    ) -> dict:
        """用户同意现生成 → 生成+注册 → 重规划 → workflow 响应（带『已生成X工具』提示）。"""
        try:
            gen = ToolGenesisService.generate_and_register(db, domain_id, offer, user_id, content)
        except Exception as e:
            logger.error(f"[ChatService] 现生成异常: {type(e).__name__}: {e}")
            gen = {"ok": False, "reason": f"现生成异常: {e}"}

        if not gen.get("ok"):
            return {
                "type": "clarification",
                "content": (
                    f"抱歉，现生成脚本没成功（{gen.get('reason', '未知原因')}）。\n"
                    "可以换个说法再试，或者我按现有能力帮你看看有没有别的路子。"
                ),
                "data": "",
            }

        tool_id = gen["tool_id"]
        tool_name = gen.get("name") or tool_id
        reused = gen.get("reused")
        available = offer.get("available") or []
        goals = offer.get("goals") or []
        input_names = ChatService._format_data_type_names(available)
        goal_names = ChatService._format_data_type_names(goals)

        # 重规划：工具图已含新工具（generate_and_register 内已 invalidate）
        candidates = PlannerService.plan_workflow(db, domain_id, available, goals)

        if not candidates:
            lead = "已存在" if reused else "已生成"
            return {
                "type": "clarification",
                "content": (
                    f"{lead}单步工具「{tool_name}」（{tool_id}）并录入脚本库，"
                    f"但暂时仍规划不出从 {input_names} 到 {goal_names} 的完整路径。\n"
                    "可能还需别的工具衔接，请补充更多细节。"
                ),
                "data": json.dumps({"codegen_done": True, "tool_id": tool_id}, ensure_ascii=False),
            }

        summary_parts = []
        for i, c in enumerate(candidates):
            summary_parts.append(
                f"**方案{i + 1}**（{len(c['tool_chain'])}步，得分 {c['score']}）：{c['explanation']}"
            )
        summary = "\n\n".join(summary_parts)
        lead = (
            f"已存在现生成工具「{tool_name}」（{tool_id}），直接复用。\n\n"
            if reused else
            f"✅ 已现生成单步工具「{tool_name}」（{tool_id}）并录入脚本库。\n\n"
        )
        return {
            "type": "workflow",
            "content": f"{lead}输入数据：{input_names}\n分析目标：{goal_names}\n\n{summary}",
            "data": json.dumps({"codegen_done": True, "tool_id": tool_id}, ensure_ascii=False),
            "available_inputs": json.dumps(available, ensure_ascii=False),
            "goal_types": json.dumps(goals, ensure_ascii=False),
            "workflow_candidates": json.dumps(candidates, ensure_ascii=False),
        }

    @staticmethod
    def _out_of_scope_response(verdict: dict) -> dict:
        """明确与生信分析无关：友好说明 + 列出能做什么。不钉领域。"""
        content = (
            "这看起来不是一个生物信息学分析任务，我暂时没法帮你处理。\n"
            "我可以做这类分析：\n"
            "- 扩增子（16S / ITS）测序：ASV 推断、物种注释、Alpha/Beta 多样性、差异分析等\n\n"
            "如果你的需求属于上面这些，请描述你的数据（如双端 FASTQ）和分析目标，我来帮你规划流程。"
        )
        return {"type": "clarification", "content": content, "data": ""}

    @staticmethod
    def _disambiguate_response(candidates: list[dict]) -> dict:
        """多库低置信：列出候选领域请用户确认。不钉领域（T4）。"""
        lines = []
        for i, c in enumerate(candidates):
            desc = (c.get("description") or "").strip()
            head = c.get("name") or c.get("code")
            lines.append(f"{i + 1}. **{head}**" + (f"：{desc}" if desc else ""))
        content = (
            "你的需求可能涉及以下几个方向，能帮我确认一下吗？\n\n"
            + "\n".join(lines)
            + "\n\n请告诉我更具体的数据和分析目标，我好为你选对方向。"
        )
        return {"type": "clarification", "content": content, "data": ""}

    @staticmethod
    def _uncertain_response(verdict: dict | None) -> dict:
        """不确定是否相关：追问引导。不钉领域、不硬拒（衔接 T5 重判）。"""
        content = (
            "我想先确认一下你的需求，好选对分析方向。\n"
            "请简单说明：\n"
            "- 你有什么数据？（如双端测序 FASTQ、ASV 表、FASTA 序列）\n"
            "- 你想得到什么结果？（如物种组成、多样性、组间差异）\n\n"
            "例如「我有双端 16S 测序数据，想做物种注释和多样性分析」。"
        )
        return {"type": "clarification", "content": content, "data": ""}

    @staticmethod
    def _path_confirmed(db: Session, task_id: int) -> bool:
        """是否已确认过分析路径（存在 confirm_path 产生的 select_path 消息）。
        确认后领域锁定，不再重判（T5）。"""
        return Message.where(db, task_id=task_id, type="select_path").first() is not None

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
        # history 含刚 save 的当前用户消息；IntentAgent/澄清把它作为 content 单独传，
        # 故历史里排除最后一条（当前消息），避免"两条连续 user 消息"让模型回裸消息的默认行为。
        history_dicts = ChatService._build_history_dicts(history[:-1])

        # 期三+T4+T5：领域分流 + 相关性闸 + 多库消歧 + 早期重判。
        verdict = None
        candidates: list[dict] = []
        path_confirmed = bool(task.domain_id) and ChatService._path_confirmed(db, task.id)

        if task.domain_id and path_confirmed:
            # 路径已确认：领域锁定，不再重判
            domain = DomainService.get(db, task.domain_id)
        elif task.domain_id:
            # 已钉但路径未确认：允许早期重判（用户可能改口到别的领域）
            verdict = DomainClassifier.classify_with_relevance(db, combined_content)
            logger.info(f"[ChatService] 早期重判: {verdict}")
            candidates = verdict.get("candidates") or []
            if (verdict["in_scope"] and verdict["domain_id"]
                    and verdict["domain_id"] != task.domain_id
                    and verdict["confidence"] in ("high", "medium")):
                logger.info(f"[ChatService] 领域切换: {task.domain_id} -> {verdict['domain_id']}")
                task.domain_id = verdict["domain_id"]
                task.save(db)
                domain = DomainService.get(db, task.domain_id)
                history_dicts = []  # 换领域后从零解析，避免旧领域上下文污染
            else:
                # 维持原领域（同领域 / 更弱信号）
                domain = DomainService.get(db, task.domain_id)
                verdict = None
                candidates = []
        else:
            # 首次：跑相关性闸
            verdict = DomainClassifier.classify_with_relevance(db, combined_content)
            logger.info(f"[ChatService] 领域判定: {verdict}")
            candidates = verdict.get("candidates") or []
            # 钉领域条件：in_scope 且（高置信，或只有一个可信候选）。
            # 多库低置信（≥2 候选）时不钉，先让用户消歧（T4）。
            if verdict["in_scope"] and not (
                verdict["confidence"] in ("medium", "low") and len(candidates) >= 2
            ):
                task.domain_id = verdict["domain_id"]
                task.save(db)
                domain = DomainService.get(db, task.domain_id)
            else:
                domain = None

        domain_id = task.domain_id  # 领域已定时即当前 task.domain_id（已钉/刚钉/刚切换）

        # Path B 生成提议响应优先：「好/生成吧」这类回复不是生信查询，会被相关性闸判出 B 路，
        # 故在正常 dispatch 前先拦截（同意 → 现生成；拒绝 → 礼貌收尾；其他 → 落到正常分流）。
        _standalone_resp = None
        _pending_standalone = ChatService._pending_standalone_offer(history)
        if _pending_standalone is not None:
            _acceptance = ChatService._judge_codegen_acceptance(combined_content)
            logger.info(f"[ChatService] standalone 生成提议待响应，判定: {_acceptance}")
            if _acceptance == "accept":
                _standalone_resp = ChatService._handle_standalone_generate(
                    db, _pending_standalone, combined_content, task, user_id
                )
            elif _acceptance == "decline":
                _standalone_resp = {
                    "type": "clarification",
                    "content": "好的，先不生成。需要的时候随时跟我说。",
                    "data": "",
                }

        # 意图识别 + 路由：仅在通过相关性闸（领域已定）时进行
        if _standalone_resp is not None:
            ai_response = _standalone_resp
        elif domain is not None:
            # Phase 3：若上一轮是能力缺口提议，本轮先判是否同意现生成
            offer = ChatService._pending_codegen_offer(history)
            if offer is not None:
                acceptance = ChatService._judge_codegen_acceptance(combined_content)
                logger.info(f"[ChatService] 缺口提议待响应，用户回复判定: {acceptance}")
                if acceptance == "accept":
                    ai_response = ChatService._handle_codegen_accept(
                        db, domain_id, offer, combined_content, user_id
                    )
                else:
                    # decline/other：当作新一轮发言重新理解意图（用户可能改主意/补充/提问）
                    ai_response = ChatService._default_intent_route(
                        db, domain, domain_id, combined_content, history_dicts, task, user_message, history
                    )
            else:
                ai_response = ChatService._default_intent_route(
                    db, domain, domain_id, combined_content, history_dicts, task, user_message, history
                )
        elif verdict and verdict.get("in_scope") and len(verdict.get("candidates") or []) >= 2:
            # 多库低置信：列出候选领域请用户确认，不钉领域（T4）
            ai_response = ChatService._disambiguate_response(verdict["candidates"])
        elif verdict and verdict.get("plausible_bioinfo"):
            # 合理生信但不属于任何 typed 领域（且无多库歧义）→ Path B 候选：
            # 形态判定器区分单步(standalone)与多步(pipeline)。单步走 B 独立闭环，
            # 多步保守归 uncertain（老路 planner 需 typed 领域，此处无，先追问引导）。
            form = AnalysisRouter.classify_form(combined_content, verdict)
            if form.get("form") == "standalone":
                ai_response = ChatService._standalone_route(
                    db, combined_content, history_dicts, task, user_id, verdict, form
                )
            else:
                ai_response = ChatService._uncertain_response(verdict)
        elif verdict and verdict["confidence"] == "high":
            # 明确与生信分析无关：友好拒绝，不钉领域（task.domain_id 保持 NULL）
            ai_response = ChatService._out_of_scope_response(verdict)
        else:
            # 不确定（medium/low/uncertain 或无启用领域）：追问引导，不钉领域、不硬拒（衔接 T5）
            ai_response = ChatService._uncertain_response(verdict)

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

        # 期三：读取任务所属领域（旧任务回退 amplicon）
        domain_id = task.domain_id or DomainService.get_amplicon_domain(db).id

        # 确定必需文件
        required_files = DomainService.resolve_required_files(db, domain_id, tool_ids)
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

    # ─── Reference markdown directory for Amplicon tools ───
    _AMPLICON_REF_DIR = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "Amplicon", "reference")
    )

    @staticmethod
    def _load_tool_reference_md(tool_id: str) -> str | None:
        """根据 tool_id 加载 scripts/Amplicon/reference 下对应的 markdown 文档。"""
        if not tool_id or not tool_id.startswith("amp-"):
            return None
        name = tool_id[4:]
        if not os.path.isdir(ChatService._AMPLICON_REF_DIR):
            return None
        # tool_id 用连字符（如 amp-frags-qc），而参考文档文件名用下划线
        # （如 step2_frags_qc.md）。两种形式都尝试匹配尾缀，否则连字符工具
        # 会拿不到文档、LLM 只能退化成 cp 占位。
        name_variants = [name, name.replace("-", "_"), name.replace("_", "-")]
        candidates = [
            f for f in os.listdir(ChatService._AMPLICON_REF_DIR)
            if f.endswith(".md") and any(f.endswith(f"_{v}.md") for v in name_variants)
        ]
        if not candidates:
            return None
        try:
            with open(os.path.join(ChatService._AMPLICON_REF_DIR, candidates[0]), "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"[ChatService] 读取 {tool_id} 参考文档失败: {e}")
            return None

    @staticmethod
    def _build_tool_contract(tid: str, call_def, tool_name: str) -> str:
        """从 DB ScriptCallDef 构造紧凑调用契约（几行），替代整篇 .md 喂给 LLM。

        给出：脚本路径、必含的 -o 输出目录、参数（flag + 取值/消费的上游类型）、
        产物文件名（相对 -o 目录）。让 LLM 拿到确定性的文件名，无需 rename/symlink 兜底，
        也无需照搬 .md 散文，从而大幅精简输出。
        """
        lines = [f"### {tool_name} (tool_id={tid})"]
        lines.append(f"调用: bash ${{AMPLICON_ROOT}}/{call_def.script_path}")
        out_dir = ""
        for p in call_def.params:
            if p.data_type == "_OUTPUT_DIR":
                out_dir = p.default or ""
                break
        if out_dir:
            lines.append(f"必含: -o {out_dir}   （产物写入该目录）")
        pparts = []
        for p in call_def.params:
            dt = p.data_type
            if dt == "_OUTPUT_DIR":
                continue
            if dt == "_MANIFEST":
                pparts.append(f"{p.flag} manifest.tsv")
            elif dt == "_CONFIG":
                pparts.append(f"{p.flag} {p.default}" if p.default else f"{p.flag} <值>")
            elif dt == "_PRIMER_F":
                pparts.append(f"{p.flag} <正向引物>")
            elif dt == "_PRIMER_R":
                pparts.append(f"{p.flag} <反向引物>")
            elif dt == "_METADATA":
                pparts.append(f"{p.flag} <metadata文件>")
            elif dt == "_GROUP_LIST":
                pparts.append(f"{p.flag} group.list")
            elif dt.startswith("_"):
                if p.default:
                    pparts.append(f"{p.flag} {p.default}")
            else:
                # 普通数据类型：标明消费的上游产物类型，LLM 据此衔接上一步 -o 目录里的文件
                pparts.append(f"{p.flag} <{dt}>")
        if pparts:
            lines.append("参数: " + "  ".join(pparts))
        if call_def.outputs:
            outs = ", ".join(
                (f"{o.data_type}=<目录模式，下游用上一步 -o 目录引用>" if not o.filename else f"{o.data_type}={o.filename}")
                for o in call_def.outputs
            )
            where = f"（相对 {out_dir}/）" if out_dir else ""
            lines.append(f"产物{where}: {outs}")
        if getattr(call_def, "per_sample", False):
            lines.append("注: per-sample，按样本循环；filename 里的 ${sample} 用样本变量替换")
        return "\n".join(lines)

    @staticmethod
    def _load_tool_source(script_path: str) -> str:
        """读取节点 .sh 源码，喂给 LLM 理解参数语义/隐含机制（哪些参数可省、
        脚本如何从输入 basename 反推样本名、目录模式产物如何被消费）。

        script_path 形如 "Amplicon/scripts/step1_cutadapt.sh"，相对后端根的 scripts/ 目录。
        """
        backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full = os.path.join(backend_root, "scripts", script_path)
        try:
            with open(full, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"[ChatService] 读取脚本源码失败 {script_path}: {e}")
            return ""

    @staticmethod
    def _generate_orchestrator_with_llm(
        tool_ids: list[str],
        tool_chain: list[dict],
        file_mappings: list[dict],
        required_files: list[dict],
        extra_params: dict | None = None,
        task_id: int | None = None,
        param_overrides: dict | None = None,
        call_defs: dict | None = None,
    ) -> str | None:
        """根据工具链参考文档，用 LLM 生成完整 bash 编排脚本。"""
        if not tool_ids:
            return None

        try:
            if not DASHSCOPE_API_KEY:
                logger.warning("[ChatService] DASHSCOPE_API_KEY 为空，跳过 LLM 编排脚本生成")
                return None

            extra = extra_params or {}

            # ─── 构造每个工具的【契约 + .sh 源码】───
            # 契约（脚本路径/-o/参数/产物文件名）钉死文件名与接线，防 LLM 编造；
            # .sh 源码让 LLM 理解参数语义/隐含机制（哪些可省、basename 抽样、目录模式），
            # 构成与算法路（纯规则读契约）的真正对照——两路用不同方式理解同一流程。
            cd_map = call_defs or {}
            md_sections = []
            for tid in tool_ids:
                tool_info = next((t for t in tool_chain if isinstance(t, dict) and t.get("id") == tid), {})
                tool_name = tool_info.get("name") or tool_info.get("label") or tid
                cd = cd_map.get(tid)
                if cd:
                    block = ChatService._build_tool_contract(tid, cd, tool_name)
                    src = ChatService._load_tool_source(cd.script_path)
                    if src:
                        block += (
                            f"\n源码 {cd.script_path}（理解参数语义/隐含机制用；"
                            f"文件名与接线仍以契约为准，勿照搬源码散文）:\n```bash\n{src}\n```"
                        )
                    md_sections.append(block)
                else:
                    # 回退：DB 无契约时读 .md 原文（极少发生）
                    md = ChatService._load_tool_reference_md(tid)
                    if md:
                        md_sections.append(f"## 工具: {tool_name} (tool_id={tid})\n{md}\n")
                    else:
                        md_sections.append(
                            f"### {tool_name} (tool_id={tid})\n"
                            f"输入类型: {tool_info.get('inputs', [])}\n"
                            f"输出类型: {tool_info.get('outputs', [])}\n"
                        )
            docs_content = "\n".join(md_sections)

            # ─── 构造工具链摘要 ───
            chain_lines = []
            for i, tid in enumerate(tool_ids, start=1):
                tool_info = next((t for t in tool_chain if isinstance(t, dict) and t.get("id") == tid), {})
                name = tool_info.get("name") or tool_info.get("label") or tid
                inputs = tool_info.get("inputs", [])
                outputs = tool_info.get("outputs", [])
                chain_lines.append(
                    f"步骤 {i}/{len(tool_ids)}: {name} (tool_id={tid})\n"
                    f"  输入数据类型: {inputs}\n"
                    f"  输出数据类型: {outputs}"
                )
            chain_summary = "\n".join(chain_lines)

            # ─── 构造上传文件描述 ───
            upload_lines = []
            for fm in file_mappings:
                upload_lines.append(
                    f"- slot_label={fm.get('slot_label')}, "
                    f"original_name={fm.get('original_name')}, "
                    f"stored_name={fm.get('stored_name')}"
                )
            upload_desc = "\n".join(upload_lines) or "无"

            # ─── 预计算「样本映射」+「自动派生文件」（既定事实，喂给 LLM，与算法路同源）───
            # LLM 不再自己从文件名猜样本名 / 编 group.list，而是原样使用这两段确定性产物。
            samples = _resolve_fastq_pair_uploads(file_mappings, required_files)
            sample_mapping_block = build_sample_mapping_block(samples)
            derived_block = build_derived_files_block(extra.get("metadata_stored", ""), tool_ids, cd_map)

            # ─── 构造 required_files 描述 ───
            rf_lines = []
            for rf in required_files:
                rf_lines.append(
                    f"- label={rf.get('label')}, typeId={rf.get('typeId')}, "
                    f"extensions={rf.get('extensions', [])}, required={rf.get('required', True)}"
                )
            required_files_desc = "\n".join(rf_lines) or "无"

            # ─── 构造用户修改的参数描述（让 LLM 也用用户改的值，对比才公平）───
            ovr = param_overrides or {}
            ovr_lines = []
            for tid in tool_ids:
                if ovr.get(tid):
                    flags = ", ".join(f"{k}={v}" for k, v in ovr[tid].items())
                    ovr_lines.append(f"- {tid}: {flags}")
            param_overrides_desc = "\n".join(ovr_lines) or "无"

            system_prompt = """你是一个生物信息分析流程编排专家。根据下方【工具调用契约】（每个工具都附了它的 .sh 源码）和【已确定的样本/文件映射】生成一个完整可执行的 bash 脚本。

【关于附带的源码——用来理解全貌】
- 契约段里每个工具都附了它的 .sh 源码。读源码以理解参数的真实语义和隐含机制：哪些参数可省（如可选的参考数据库 -d，不传则脚本跳过该子功能）、脚本如何从输入文件 basename 反推样本名、目录模式产物如何被消费、-g 需要什么格式的清单。
- 但【文件名和接线以契约为准】，源码只帮你理解"为什么这样接"；不要照搬源码里的 echo/usage/软件验证/cleanup 等散文，不要编造契约外的文件名。

【工具间衔接——最重要的规则】
1. 每个工具强制 -o <Tool>_Output，产物写入该目录。
2. 本步参数消费的数据类型 <DT> 等于上一步某产物的数据类型时，本步该参数指向上一步产物。两种情形：
   (a) 产物有具体 filename → 指向「上一步 -o 目录/filename」，如 -i DADA2_Output/featureSeqs.qza；
   (b) 产物标注「目录模式」(filename 为空) → 该类型即上一步整个 -o 目录，本步参数直接指向上一步 -o 目录本身，如 -i BetaData_Output/。
   绝不编造契约里没有的文件名。

【样本与文件映射——已确定，禁止从文件名猜测】
3. 上传文件存为哈希名(stored_name)，磁盘即 /shared/<stored_name>；用户原始文件名 original_name 只用来确定样本归属。
4. 「样本与文件映射」段已给出 declare -A R1_OF R2_OF 和 SAMPLES=() —— 这是唯一真值来源，原样保留到脚本，不要写任何"从文件名解析样本名"的逻辑。

【per-sample 区】
5. per-sample 工具(cutadapt/flash/frags_qc 等契约标注 per-sample 者)从【输入文件 basename】反推样本名。哈希名直接喂会抽出哈希、产出哈希名文件，下游按样本名找不到而断链。故每个样本循环体开头必须先把哈希文件软链规范化：
     ln -sf "${R1_OF[$SAMPLE]}" "${SAMPLE}.R1.fastq.gz"
     ln -sf "${R2_OF[$SAMPLE]}" "${SAMPLE}.R2.fastq.gz"
   然后 cutadapt 用 -r1 "${SAMPLE}.R1.fastq.gz"。basename 才能抽出 $SAMPLE，全链命名一致。
6. 所有 per-sample 工具融合进【唯一一个】按样本并行区，每样本在同一个 ( ... ) & 子shell 内顺序跑完；产物 filename 里的 ${sample} 用 $SAMPLE 替换。禁止为每个 per-sample 工具各开一个 for 循环。

【manifest 与自动派生文件——已预生成，原样保留】
7. 契约含 manifest 的工具（如 DADA2）：在 per-sample 区 wait 之后，生成 manifest.tsv(每样本一行：sample-id<TAB>$(pwd)/<上一步 QC 产物路径>)，再调用该工具。
8. group.list / vs.list / rf.list 无节点产出。「自动派生文件」段已给出从 metadata 生成它们的代码，原样放在脚本头部。契约里 -g group.list 直接引用 group.list，【不要】把 metadata 传给 -g。

【输出】
9. #!/bin/bash 开头，set -euo pipefail，顶部 export PATH=/opt/conda/bin:$PATH 和 AMPLICON_ROOT=/opt/amplicon。
10. 只输出 bash 脚本，不要解释、不要 markdown 代码块。简洁：必要变量 + 每步 bash 调用行 + 简短进度 echo；禁止照抄契约原文、禁止大段行内注释。"""

            user_message = f"""请根据以下信息生成完整的执行脚本：

## 任务ID
{task_id or 'N/A'}

## 工具链（按执行顺序）
{chain_summary}

## 用户上传文件
{upload_desc}

## 样本与文件映射（已确定，原样保留到脚本；禁止从文件名猜样本名）
{sample_mapping_block or "（无 FASTQ_PAIR 上传，本链路无 per-sample 样本）"}

## 自动派生文件（原样放脚本头部；契约里 -g group.list 等直接引用，不要传 metadata）
{derived_block or "（本链路无需 group.list/vs.list/rf.list）"}

## 文件需求定义
{required_files_desc}

## 额外参数
- primer_f: {extra.get('primer_f', '')}
- primer_r: {extra.get('primer_r', '')}
- metadata_stored: {extra.get('metadata_stored', '')}

## 用户修改的参数（必须使用这些值，覆盖参考文档默认值）
{param_overrides_desc}

## 各工具调用契约（结构化：脚本路径 / -o 输出目录 / 参数 / 产物文件名）
{docs_content}

请生成一个把这些工具串联起来的完整 bash 脚本，确保每一步的输入输出正确衔接。"""

            prompt_size = len(system_prompt) + len(user_message)
            logger.info(f"[ChatService] 开始 LLM 编排脚本生成: {len(tool_ids)} 个工具, prompt={prompt_size} 字符")

            codegen_timeout = max(LLM_CODEGEN_TIMEOUT, 300)
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
            usage = result.get("usage", {})
            logger.info(
                f"[ChatService] LLM 编排 token: "
                f"prompt={usage.get('prompt_tokens')} "
                f"completion={usage.get('completion_tokens')} "
                f"total={usage.get('total_tokens')}"
            )
            generated = result["choices"][0]["message"]["content"]

            # 去掉可能的 markdown 代码块包裹
            if "```bash" in generated:
                generated = generated.split("```bash", 1)[1].split("```", 1)[0]
            elif "```" in generated:
                generated = generated.split("```", 1)[1].split("```", 1)[0]

            generated = generated.strip()
            logger.info(f"[ChatService] LLM 编排脚本生成完成: {len(generated)} 字符")
            return generated

        except Exception as e:
            import traceback
            logger.error(f"[ChatService] LLM 编排脚本生成失败: {type(e).__name__}: {e}")
            logger.error(traceback.format_exc())
            return None

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

4. **用户上传文件**：用户上传的文件存放在 `/shared/` 目录下，文件名使用系统存储的哈希名（stored_name，形如 `abc123def.gz`），用 `/shared/<stored_name>` 引用。

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
        candidate: dict = {}
        tool_chain: list[dict] = []
        param_overrides: dict = {}
        try:
            candidate = json.loads(candidate_data_str)
            tool_chain = candidate.get("tool_chain", []) if isinstance(candidate, dict) else []
            if not tool_ids:
                tool_ids = [t["id"] for t in tool_chain if isinstance(t, dict) and "id" in t]
            # 提取用户在节点上改的参数（已校验防注入）
            param_overrides = _sanitize_param_overrides(tool_chain)
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

        generated_code_algo = ""
        generated_code_llm = ""
        algo_error = ""   # 非空 = 算法路径失败（脚本保持空，绝不把错误文字当脚本）
        llm_error = ""    # 非空 = LLM 路径失败
        call_defs = {}    # 算法路填充；LLM 路复用同一份 DB 契约（算法路异常时保持空，LLM 回退 .md）
        if tool_ids:
            # ─── 1. 算法生成编排脚本 ───
            try:
                # 期三：读取任务所属领域（旧任务回退 amplicon）
                domain_id = task.domain_id or DomainService.get_amplicon_domain(db).id
                call_defs = DomainService.get_call_defs(db, domain_id, tool_ids)
                tool_names = DomainService.get_tool_names(db, domain_id)
                generated_code_algo = generate_orchestrator_script(
                    tool_ids=tool_ids,
                    call_defs=call_defs,
                    tool_names=tool_names,
                    file_mappings=enriched_mappings,
                    required_files=required_files_info,
                    extra_params=extra_params,
                    task_id=task.id,
                    param_overrides=param_overrides,
                )
                logger.info(f"[ChatService] 算法编排脚本生成完成: {len(generated_code_algo)} 字符")
            except Exception as e:
                logger.error(f"[ChatService] 算法编排脚本生成失败: {e}")
                algo_error = f"{type(e).__name__}: {e}"

            # ─── 2. LLM 生成编排脚本 ───
            try:
                llm_out = ChatService._generate_orchestrator_with_llm(
                    tool_ids=tool_ids,
                    tool_chain=tool_chain,
                    call_defs=call_defs,
                    file_mappings=enriched_mappings,
                    required_files=required_files_info,
                    extra_params=extra_params,
                    task_id=task.id,
                    param_overrides=param_overrides,
                )
                if llm_out:
                    generated_code_llm = llm_out
                else:
                    llm_error = "未返回内容（可能未配置 API Key、网络超时、限流或模型返回为空）"
            except Exception as e:
                logger.error(f"[ChatService] LLM 编排脚本生成调用失败: {e}")
                llm_error = f"{type(e).__name__}: {e}"

        # 失败时不把错误塞进脚本字符串（避免被当真脚本执行 → 注释脚本秒成功），
        # 而是单独记录 status/errors，供 start_execution 拦截、供消息文案如实展示。
        result_payload = json.dumps({
            "script1": generated_code_algo,
            "script2": generated_code_llm,
            "status": {
                "script1": "failed" if algo_error else ("ok" if generated_code_algo else "empty"),
                "script2": "failed" if llm_error else ("ok" if generated_code_llm else "empty"),
            },
            "errors": {"script1": algo_error, "script2": llm_error},
        }, ensure_ascii=False)

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

        # 创建助手消息（校验通过 + 两份编排脚本的真实生成状态：失败时如实告警）
        def _code_status_line(label: str, code: str, error: str) -> str:
            if error:
                return f"• {label}: ❌ 生成失败 — {error}"
            if code:
                return f"• {label}: ✅ 已生成"
            return f"• {label}: ⚠ 未生成"

        algo_ok = bool(generated_code_algo) and not algo_error
        llm_ok = bool(generated_code_llm) and not llm_error
        any_ok = algo_ok or llm_ok
        assistant_content = (
            "✅ 文件校验完成！\n\n"
            "• 文件格式: 正确\n"
            "• 文件完整性: 通过\n"
            + _code_status_line("执行代码1（算法编排）", generated_code_algo, algo_error) + "\n"
            + _code_status_line("执行代码2（LLM 编排）", generated_code_llm, llm_error) + "\n\n"
            + ("已就绪的代码可以开始执行分析任务。" if any_ok
               else "❌ 两份代码均未生成，暂时无法执行分析任务，请检查后端日志或重试。")
        )
        assistant_message = Message(
            task_id=task.id,
            role="assistant",
            type="text",
            content=assistant_content,
            data=json.dumps({"upload_validated": True}, ensure_ascii=False),
            result_content=result_payload,
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
        script_index: int = 1,
    ) -> dict:
        """提交 qsub 任务执行"""
        task = ChatService._get_or_create_task(db, None, task_uuid, project_id, user_id)

        if task.status in ("running", "completed"):
            raise ValueError(f"任务当前状态为 {task.status}，不可重复执行")

        logger.info(f"[ChatService] 开始执行: task={task.id}, script_index={script_index}")

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

        # 优先使用生成的真实代码；支持双脚本 JSON 结构 {script1, script2}
        generated_code = ""
        gen_failed_reason = ""   # 非空 = 该脚本是已知生成失败，应拒绝执行而非静默模拟
        source_message = None
        if validated_message and validated_message.result_content:
            source_message = validated_message
        elif fr_message and fr_message.result_content:
            source_message = fr_message

        if source_message and source_message.result_content:
            raw_content = source_message.result_content
            try:
                parsed = json.loads(raw_content)
                if isinstance(parsed, dict):
                    key = f"script{script_index}"
                    generated_code = parsed.get(key, "")
                    # 兜底：如果指定 key 不存在，使用整个原始内容（兼容旧数据）
                    if not generated_code:
                        generated_code = raw_content
                    # 失败拦截：confirm_upload 记录过该脚本生成失败 → 拒绝执行
                    status_map = parsed.get("status")
                    if isinstance(status_map, dict) and status_map.get(key) == "failed":
                        errors_map = parsed.get("errors")
                        gen_failed_reason = errors_map.get(key, "") if isinstance(errors_map, dict) else ""
                        if not gen_failed_reason:
                            gen_failed_reason = "生成失败（原因未记录）"
                else:
                    generated_code = raw_content
            except (json.JSONDecodeError, TypeError):
                generated_code = raw_content

        if gen_failed_reason:
            # 不静默跑注释脚本/模拟，直接报错让前端 toast 提示
            raise ValueError(
                f"执行代码{script_index} 生成失败，已拒绝执行：{gen_failed_reason}。"
                f"请回到对话查看失败提示并重试。"
            )

        if generated_code:
            script = sge_header + "\n"
            if file_env_lines:
                script += "# 上传文件路径\n" + "\n".join(file_env_lines) + "\n\n"
            script += generated_code
            logger.info(f"[ChatService] 使用生成的真实代码 (script_index={script_index}, length={len(generated_code)})")
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
