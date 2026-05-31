import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.http.controllers import ChatController
from app.http.middleware import Auth
from app.http.requests.chat_request import ConfirmPathRequest
from app.http.requests.message_request import ConfirmUploadRequest
from app.models import User
from database import get_db

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/")
def chat(
    project_id: int = Form(...),
    content: str = Form(...),
    task_id: Optional[int] = Form(None),
    task_uuid: Optional[str] = Form(None),
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
        task_uuid=task_uuid,
        image_ids=parsed_image_ids,
        images=images,
    )


@router.post("/confirm-path")
def confirm_path(
    request: ConfirmPathRequest,
    current_user: User = Auth,
    db: Session = Depends(get_db),
):
    return ChatController.confirm_path(
        task_uuid=request.task_uuid,
        project_id=request.project_id,
        candidate_id=request.candidate_id,
        candidate_data=request.candidate_data,
        user_id=current_user.id,
        db=db,
    )


@router.post("/confirm-upload")
def confirm_upload(
    request: ConfirmUploadRequest,
    current_user: User = Auth,
    db: Session = Depends(get_db),
):
    return ChatController.confirm_upload(
        task_uuid=request.task_uuid,
        project_id=request.project_id,
        file_mappings=[fm.model_dump() for fm in request.file_mappings],
        user_id=current_user.id,
        db=db,
    )
