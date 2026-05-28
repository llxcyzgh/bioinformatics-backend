import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.http.controllers import ChatController
from app.http.middleware import Auth
from app.models import User
from database import get_db

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/")
def chat(
    project_id: int = Form(...),
    content: str = Form(...),
    task_id: Optional[int] = Form(None),
    type: str = Form("text"),
    image_ids: Optional[str] = Form(None),
    images: Optional[list[UploadFile]] = File(None),
    current_user: User = Auth,
    db: Session = Depends(get_db),
):
    parsed_image_ids = None
    if image_ids:
        try:
            parsed_image_ids = json.loads(image_ids)
        except (json.JSONDecodeError, TypeError):
            parsed_image_ids = None

    return ChatController.chat(
        project_id=project_id,
        content=content,
        msg_type=type,
        user_id=current_user.id,
        db=db,
        task_id=task_id,
        image_ids=parsed_image_ids,
        images=images,
    )
