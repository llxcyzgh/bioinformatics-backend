import os
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models.model import Model
from pkg.helpers.time_helper import get_utc_now


class UploadedFile(Model):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    deleted_at = Column(Integer, default=0, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=0)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, default=0)
    original_name = Column(String, nullable=False, default='')
    stored_name = Column(String, nullable=False, default='')
    file_path = Column(String, nullable=False, default='')
    mime_type = Column(String, nullable=False, default='')
    size_bytes = Column(Integer, nullable=False, default=0)
    category = Column(String, nullable=False, default='')

    user = relationship("User")
    task = relationship("Task")

    def __repr__(self):
        return f"<UploadedFile {self.id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "original_name": self.original_name,
            "stored_name": self.stored_name,
            "file_path": self.file_path,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
