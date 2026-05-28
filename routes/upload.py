from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.http.controllers.upload_controller import UploadController
from app.http.middleware import Auth
from app.models import User
from database import get_db

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/")
def upload(
    file: UploadFile = File(...),
    task_id: int = Form(default=0),
    current_user: User = Auth,
    db: Session = Depends(get_db),
):
    return UploadController.upload(file, current_user.id, db, task_id)


@router.get("/")
def list_files(
    category: Optional[str] = None,
    task_id: Optional[int] = None,
    current_user: User = Auth,
    db: Session = Depends(get_db),
):
    return UploadController.list_files(current_user.id, db, category, task_id)


@router.get("/{file_id}/download")
def download(file_id: int, current_user: User = Auth, db: Session = Depends(get_db)):
    return UploadController.download(file_id, current_user.id, db)


@router.delete("/{file_id}")
def delete(file_id: int, current_user: User = Auth, db: Session = Depends(get_db)):
    return UploadController.delete(file_id, current_user.id, db)
