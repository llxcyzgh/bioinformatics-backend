import logging
import os
import subprocess
import uuid
from typing import Optional

import httpx
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.upload import UploadedFile
from config.upload import UPLOAD_DIR, MAX_UPLOAD_SIZE_MB, ALLOWED_IMAGE_EXTENSIONS, ALLOWED_ALL_EXTENSIONS, ARCHIVE_EXTENSIONS

logger = logging.getLogger(__name__)


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

        ok, err_msg = UploadService.validate_archive_integrity(full_path, file.filename)
        if not ok:
            os.remove(full_path)
            raise ValueError(f"文件已上传但校验失败，请检查文件是否损坏后重新上传。{err_msg}")

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
    def list_by_user(db: Session, user_id: int, category: Optional[str] = None, task_id: Optional[int] = None, project_id: Optional[int] = None, search: Optional[str] = None) -> list:
        from app.models import Task
        query = db.query(UploadedFile).filter(UploadedFile.user_id == user_id, UploadedFile.deleted_at == 0)
        if category:
            query = query.filter(UploadedFile.category == category)
        if task_id is not None:
            query = query.filter(UploadedFile.task_id == task_id)
        if project_id is not None:
            query = query.join(Task, UploadedFile.task_id == Task.id).filter(Task.project_id == project_id)
        if search:
            query = query.filter(UploadedFile.original_name.ilike(f"%{search}%"))
        return query.order_by(UploadedFile.id.desc()).all()

    @staticmethod
    def validate_archive_integrity(file_path: str, original_name: str = "") -> tuple[bool, str]:
        """
        校验压缩文件完整性。使用 7z t 命令检测。
        非压缩文件直接返回通过。
        返回 (ok, error_msg)。
        """
        lower_name = original_name.lower() if original_name else file_path.lower()
        is_archive = any(lower_name.endswith(ext) for ext in ARCHIVE_EXTENSIONS)
        if not is_archive:
            return True, ""

        try:
            result = subprocess.run(
                ["7z", "t", file_path],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                return True, ""
            else:
                err = (result.stderr or result.stdout or "").strip()[:200]
                return False, f"压缩文件完整性校验失败: {err or '未知错误'}"
        except FileNotFoundError:
            logger.warning("7z 命令未找到，跳过压缩文件完整性校验")
            return True, ""
        except subprocess.TimeoutExpired:
            return False, "压缩文件完整性校验超时（文件可能过大）"
