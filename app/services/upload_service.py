import os
import uuid
from typing import Optional

import httpx
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.upload import UploadedFile
from config.upload import UPLOAD_DIR, MAX_UPLOAD_SIZE_MB, ALLOWED_IMAGE_EXTENSIONS, ALLOWED_ALL_EXTENSIONS


class UploadService:

    @staticmethod
    def _get_category(filename: str) -> str:
        ext = UploadService._get_ext(filename)
        if ext in ALLOWED_IMAGE_EXTENSIONS:
            return "image"
        return "data"

    @staticmethod
    def _get_ext(filename: str) -> str:
        name = filename.lower()
        if name.endswith(".tar.gz"):
            return ".tar.gz"
        return os.path.splitext(name)[1]

    @staticmethod
    def _validate_file(file: UploadFile) -> str:
        if not file.filename:
            raise ValueError("文件名不能为空")

        ext = UploadService._get_ext(file.filename)
        if ext not in ALLOWED_ALL_EXTENSIONS:
            raise ValueError(f"不支持的文件类型: {ext}")

        return ext

    @staticmethod
    def create(file: UploadFile, user_id: int, db: Session, task_id: int = 0) -> UploadedFile:
        ext = UploadService._validate_file(file)

        content = file.file.read()
        size = len(content)
        max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if size > max_bytes:
            raise ValueError(f"文件大小超过限制 ({MAX_UPLOAD_SIZE_MB}MB)")

        stored_name = f"{uuid.uuid4().hex}{ext}"
        category = UploadService._get_category(file.filename)
        user_dir = os.path.join(UPLOAD_DIR, str(user_id))
        os.makedirs(user_dir, exist_ok=True)

        full_path = os.path.join(user_dir, stored_name)
        with open(full_path, "wb") as f:
            f.write(content)

        relative_path = os.path.join(str(user_id), stored_name)

        record = UploadedFile(
            user_id=user_id,
            task_id=task_id,
            original_name=file.filename,
            stored_name=stored_name,
            file_path=relative_path,
            mime_type=file.content_type or "application/octet-stream",
            size_bytes=size,
            category=category,
        )
        return record.save(db)

    @staticmethod
    def find(db: Session, file_id: int, user_id: int) -> Optional[UploadedFile]:
        record = UploadedFile.find(db, file_id)
        if not record or record.user_id != user_id:
            return None
        return record

    @staticmethod
    def get_file_path(record: UploadedFile) -> str:
        return os.path.join(UPLOAD_DIR, record.file_path)

    @staticmethod
    def delete(db: Session, file_id: int, user_id: int) -> Optional[UploadedFile]:
        record = UploadService.find(db, file_id, user_id)
        if not record:
            return None
        record.delete(db)
        return record

    @staticmethod
    def list_by_user(db: Session, user_id: int, category: Optional[str] = None, task_id: Optional[int] = None) -> list:
        query = UploadedFile.where(db, user_id=user_id)
        if category:
            query = query.filter(UploadedFile.category == category)
        if task_id is not None:
            query = query.filter(UploadedFile.task_id == task_id)
        return query.order_by(UploadedFile.id.desc()).all()
