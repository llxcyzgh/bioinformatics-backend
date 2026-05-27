import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Task, Message
from app.services.ai_service import AIService


class ChatService:

    @staticmethod
    def _get_or_create_task(db: Session, task_id: Optional[int], project_id: int, user_id: int) -> Task:
        if task_id:
            task = Task.find(db, task_id)
            if not task:
                raise ValueError("Task not found")
            if task.user_id != user_id:
                raise ValueError("Forbidden")
            return task

        task_count = Task.where(db, project_id=project_id, user_id=user_id).count()
        task = Task(
            uuid=str(uuid.uuid4()),
            name=f"Chat {task_count + 1}",
            project_id=project_id,
            user_id=user_id,
        )
        return task.save(db)

    @staticmethod
    def chat(db: Session, task_id: Optional[int], project_id: int, content: str, msg_type: str, user_id: int) -> dict:
        task = ChatService._get_or_create_task(db, task_id, project_id, user_id)

        # Save user message
        user_message = Message(
            task_id=task.id,
            role="user",
            type=msg_type,
            content=content,
        )
        user_message.save(db)

        # Build conversation history (id asc)
        history = (
            Message.where(db, task_id=task.id)
            .order_by(Message.id.asc())
            .all()
        )

        # Call LLM
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
