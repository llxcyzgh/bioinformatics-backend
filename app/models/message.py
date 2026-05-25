from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models.model import Model
from pkg.helpers.time_helper import get_utc_now


class Message(Model):
    __tablename__ = "messages"

    # 显式定义这些字段以确保顺序 (会覆盖基类定义)
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    deleted_at = Column(Integer, default=0, nullable=False)

    # 业务字段
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, default=0)
    role = Column(String, nullable=False, default='')
    type = Column(String, nullable=False, default='')
    content = Column(Text, nullable=False, default='')
    data = Column(Text, nullable=False, default='')

    # 关系
    task = relationship("Task", backref="messages")

    def __repr__(self):
        return f"<Message {self.id}>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "role": self.role,
            "type": self.type,
            "content": self.content,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
