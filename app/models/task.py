from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models.model import Model
from pkg.helpers.time_helper import get_utc_now


class Task(Model):
    __tablename__ = "tasks"

    # 显式定义这些字段以确保顺序 (会覆盖基类定义)
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    deleted_at = Column(Integer, default=0, nullable=False)

    # 业务字段
    uuid = Column(String, unique=True, index=True, nullable=False, default='')
    name = Column(String, nullable=False, default='')
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, default=0)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=0)
    status = Column(String, nullable=False, default='pending')
    qsub_id = Column(String, nullable=False, default='')
    script_path = Column(String, nullable=False, default='')

    # 关系
    project = relationship("Project", backref="tasks")
    user = relationship("User", backref="tasks")

    def __repr__(self):
        return f"<Task {self.name}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "name": self.name,
            "user_id": self.user_id,
            "status": self.status,
            "qsub_id": self.qsub_id,
            "script_path": self.script_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
