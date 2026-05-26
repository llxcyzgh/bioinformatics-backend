from typing import List

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services import MessageService


class MessageController:
    """Message controller for conversation endpoints"""

    @staticmethod
    def index(task_id: int, db: Session, user_id: int) -> List[dict]:
        """Get all messages for a task"""
        try:
            messages = MessageService.get_messages_by_task(db, task_id, user_id)
            return [message.to_dict() for message in messages]
        except ValueError:
            return []

    @staticmethod
    def show(message_id: int, db: Session, user_id: int) -> JSONResponse:
        """Get a specific message"""
        message = MessageService.get_message_by_id(db, message_id, user_id)
        if not message:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Message not found"}
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=message.to_dict()
        )

    @staticmethod
    def store(
        task_id: int,
        type: str,
        content: str,
        data: str,
        user_id: int,
        db: Session,
    ) -> JSONResponse:
        """Create a user message and return the AI system response"""
        try:
            system_message = MessageService.create_message(
                db, task_id, type, content, data, user_id
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=system_message.to_dict()
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": str(e)}
            )

    @staticmethod
    def destroy(message_id: int, db: Session, user_id: int) -> JSONResponse:
        """Delete a message"""
        message = MessageService.get_message_by_id(db, message_id, user_id)
        if not message:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Message not found"}
            )

        MessageService.delete_message(db, message)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Message deleted successfully"}
        )
