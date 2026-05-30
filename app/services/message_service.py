from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Message, Task
from app.services.ai_service import AIService


class MessageService:
    """Message service for business logic related to messages"""

    @staticmethod
    def _verify_task_ownership(db: Session, task_id: int, user_id: int) -> Optional[Task]:
        """Verify a task exists and belongs to the given user"""
        task = Task.find(db, task_id)
        if not task or task.user_id != user_id:
            return None
        return task

    @staticmethod
    def get_messages_by_task(db: Session, task_id: int, user_id: int) -> List[Message]:
        """Get all messages for a specific task, ordered by created_at"""
        if not MessageService._verify_task_ownership(db, task_id, user_id):
            raise ValueError("Task not found")
        return (
            Message.where(db, task_id=task_id)
            .order_by(Message.created_at)
            .all()
        )

    @staticmethod
    def get_messages_by_task_uuid(db: Session, task_uuid: str, user_id: int) -> List[Message]:
        """Get all messages for a task looked up by UUID, ordered by created_at"""
        task = Task.where(db, uuid=task_uuid).first()
        if not task or task.user_id != user_id:
            raise ValueError("Task not found")
        return (
            Message.where(db, task_id=task.id)
            .order_by(Message.created_at)
            .all()
        )

    @staticmethod
    def get_message_by_id(db: Session, message_id: int, user_id: int) -> Optional[Message]:
        """Get a message by ID, verifying task ownership"""
        message = Message.find(db, message_id)
        if not message:
            return None
        if not MessageService._verify_task_ownership(db, message.task_id, user_id):
            return None
        return message

    @staticmethod
    def create_message(
        db: Session,
        task_id: int,
        type: str,
        content: str,
        data: str,
        user_id: int,
    ) -> Message:
        """Create a user message and synchronously generate an AI system response.

        Returns the system message (the AI's reply).
        """
        if not MessageService._verify_task_ownership(db, task_id, user_id):
            raise ValueError("Task not found")

        # Save user message
        user_message = Message(
            task_id=task_id,
            role='user',
            type=type,
            content=content,
            data=data,
        )
        user_message.save(db)

        # Build conversation history for the LLM
        conversation_history = (
            Message.where(db, task_id=task_id)
            .order_by(Message.created_at)
            .all()
        )

        # Generate AI response
        ai_response = AIService.generate_response(task_id, user_message, conversation_history)

        # Save system message
        system_message = Message(
            task_id=task_id,
            role='system',
            type=ai_response["type"],
            content=ai_response["content"],
            data=ai_response["data"],
        )
        system_message.save(db)

        return system_message

    @staticmethod
    def delete_message(db: Session, message: Message) -> None:
        """Soft delete a message"""
        message.delete(db)
