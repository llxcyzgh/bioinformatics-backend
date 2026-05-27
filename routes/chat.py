from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.http.controllers import ChatController
from app.http.middleware import Auth
from app.http.requests import ChatRequest
from app.models import User
from database import get_db

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/")
def chat(request: ChatRequest, current_user: User = Auth, db: Session = Depends(get_db)):
    return ChatController.chat(
        project_id=request.project_id,
        content=request.content,
        msg_type=request.type,
        user_id=current_user.id,
        db=db,
        task_id=request.task_id,
    )
