import json
import logging
import uuid
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models import Task, Message
from app.services.ai_service import AIService
from app.services.parser_service import ParserService
from app.services.planner_service import PlannerService
from app.services.upload_service import UploadService
from pkg.amplicon.amplicon_tools import DATA_TYPE_NAMES

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
                "data": json.dumps({"known_inputs": available}, ensure_ascii=False),
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
                "data": json.dumps({"known_goals": goals}, ensure_ascii=False),
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
                "data": json.dumps({"available_inputs": available, "goal_types": goals}, ensure_ascii=False),
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
            "data": json.dumps({
                "available_inputs": available,
                "goal_types": goals,
                "candidates": candidates,
            }, ensure_ascii=False),
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

        # Build user message data (image URLs)
        user_data = ""
        if all_image_urls:
            user_data = json.dumps({"images": all_image_urls}, ensure_ascii=False)

        user_message = Message(
            task_id=task.id,
            role="user",
            type=msg_type if msg_type else "text",
            content=content,
            data=user_data,
        )
        user_message.save(db)

        # Get conversation history
        history = (
            Message.where(db, task_id=task.id)
            .order_by(Message.id.asc())
            .all()
        )
        history_dicts = ChatService._build_history_dicts(history)

        # Parse user input
        try:
            parser_result = ParserService.parse(content, history_dicts)
            logger.info(f"[ChatService] 解析结果: {parser_result}")

            # Decision routing
            ai_response = ChatService._route_decision(parser_result, content, history_dicts)
        except Exception as e:
            logger.error(f"[ChatService] 解析/规划异常，回退到通用 AI: {e}")
            ai_response = AIService.generate_response(task.id, user_message, history)

        # Save AI response
        ai_message = Message(
            task_id=task.id,
            role="assistant",
            type=ai_response["type"],
            content=ai_response["content"],
            data=ai_response["data"],
        )
        ai_message.save(db)

        return {
            "task": task.to_dict(),
            "message": ai_message.to_dict(),
        }
