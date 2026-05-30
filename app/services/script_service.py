import json
import logging
import os
import uuid
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models import Script
from pkg.amplicon.amplicon_tools import DATA_TYPE_NAMES

logger = logging.getLogger(__name__)

SCRIPTS_DIR = os.getenv("SCRIPTS_DIR", "scripts")


class ScriptService:

    @staticmethod
    def list_scripts(
        db: Session,
        folder_id: Optional[int] = None,
        verified: Optional[int] = None,
        is_active: Optional[int] = None,
        tool_id: Optional[str] = None,
    ) -> list[Script]:
        query = Script.where(db)
        if folder_id is not None:
            query = query.filter(Script.folder_id == folder_id)
        if verified is not None:
            query = query.filter(Script.verified == verified)
        if is_active is not None:
            query = query.filter(Script.is_active == is_active)
        if tool_id:
            query = query.filter(Script.tool_id == tool_id)
        return query.order_by(Script.id.asc()).all()

    @staticmethod
    def get(db: Session, script_id: int) -> Script:
        script = Script.find(db, script_id)
        if not script:
            raise ValueError("Script not found")
        return script

    @staticmethod
    def get_by_tool_id(db: Session, tool_id: str) -> Optional[Script]:
        results = Script.where(db, tool_id=tool_id, is_active=1, verified=1).all()
        return results[0] if results else None

    @staticmethod
    def create(
        db: Session,
        name: str,
        folder_id: int,
        tool_id: str,
        category: str,
        file_path: str,
        uploaded_by: int,
        description: str = "",
        md_content: str = "",
        inputs: str = "[]",
        outputs: str = "[]",
        version: str = "1.0.0",
        runtime: int = 0,
        cost: float = 0.0,
        weight: int = 0,
        valid_from: str = "",
        valid_until: str = "",
    ) -> Script:
        script = Script(
            name=name,
            description=description,
            folder_id=folder_id,
            tool_id=tool_id,
            category=category,
            version=version,
            file_path=file_path,
            md_content=md_content,
            inputs=inputs,
            outputs=outputs,
            runtime=runtime,
            cost=cost,
            weight=weight,
            uploaded_by=uploaded_by,
            valid_from=valid_from,
            valid_until=valid_until,
        )
        return script.save(db)

    @staticmethod
    def upload_script(
        db: Session,
        script_file: UploadFile,
        md_file: Optional[UploadFile],
        name: str,
        folder_id: int,
        tool_id: str,
        category: str,
        uploaded_by: int,
        version: str = "1.0.0",
        runtime: int = 0,
        cost: float = 0.0,
        weight: int = 0,
        inputs: str = "[]",
        outputs: str = "[]",
        valid_from: str = "",
        valid_until: str = "",
    ) -> Script:
        # 存储脚本文件
        ext = os.path.splitext(script_file.filename)[1] if script_file.filename else ".sh"
        stored_name = f"{uuid.uuid4().hex}{ext}"
        dest_dir = os.path.join(SCRIPTS_DIR, "uploaded")
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, stored_name)

        content = script_file.file.read()
        with open(dest_path, "wb") as f:
            f.write(content)

        rel_path = f"uploaded/{stored_name}"

        # 读取 MD 文件
        md_content = ""
        if md_file:
            md_content = md_file.file.read().decode("utf-8", errors="replace")

        return ScriptService.create(
            db=db,
            name=name,
            folder_id=folder_id,
            tool_id=tool_id,
            category=category,
            file_path=rel_path,
            uploaded_by=uploaded_by,
            md_content=md_content,
            version=version,
            runtime=runtime,
            cost=cost,
            weight=weight,
            inputs=inputs,
            outputs=outputs,
            valid_from=valid_from,
            valid_until=valid_until,
        )

    @staticmethod
    def update(db: Session, script_id: int, **kwargs) -> Script:
        script = Script.find(db, script_id)
        if not script:
            raise ValueError("Script not found")
        for key, value in kwargs.items():
            if hasattr(script, key) and value is not None:
                setattr(script, key, value)
        return script.save(db)

    @staticmethod
    def verify(db: Session, script_id: int, verified_by: int) -> Script:
        script = Script.find(db, script_id)
        if not script:
            raise ValueError("Script not found")
        script.verified = 1
        script.verified_by = verified_by
        return script.save(db)

    @staticmethod
    def toggle_active(db: Session, script_id: int) -> Script:
        script = Script.find(db, script_id)
        if not script:
            raise ValueError("Script not found")
        script.is_active = 0 if script.is_active else 1
        return script.save(db)

    @staticmethod
    def delete(db: Session, script_id: int) -> dict:
        script = Script.find(db, script_id)
        if not script:
            raise ValueError("Script not found")
        script.delete(db)
        return {"detail": "Deleted"}

    @staticmethod
    def read_script_content(file_path: str) -> str:
        """读取脚本文件的完整内容"""
        full_path = os.path.join(SCRIPTS_DIR, file_path)
        if not os.path.exists(full_path):
            return ""
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
