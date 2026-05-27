from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services import ChatService


class ChatController:

    @staticmethod
    def chat(project_id: int, content: str, msg_type: str, user_id: int, db: Session, task_id: int | None = None) -> JSONResponse:
        try:
            result = ChatService.chat(db, task_id, project_id, content, msg_type, user_id)
            return JSONResponse(status_code=status.HTTP_200_OK, content=result)
        except ValueError as e:
            code = status.HTTP_403_FORBIDDEN if str(e) == "Forbidden" else status.HTTP_404_NOT_FOUND
            return JSONResponse(status_code=code, content={"detail": str(e)})
