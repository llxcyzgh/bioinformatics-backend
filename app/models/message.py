import json

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

    # 结构化字段（从 data JSON 提取）
    images = Column(Text, nullable=False, default='')
    available_inputs = Column(Text, nullable=False, default='')
    goal_types = Column(Text, nullable=False, default='')
    workflow_candidates = Column(Text, nullable=False, default='')
    required_files = Column(Text, nullable=False, default='')
    result_content = Column(Text, nullable=False, default='')
    result_files = Column(Text, nullable=False, default='')
    next_steps = Column(Text, nullable=False, default='')

    # 关系
    task = relationship("Task", backref="messages")

    def __repr__(self):
        return f"<Message {self.id}>"

    # 新列 → API 输出 key 的映射
    _COLUMN_MAP = {
        "images": "images",
        "available_inputs": "available_inputs",
        "goal_types": "goal_types",
        "workflow_candidates": "candidates",
        "required_files": "required_files",
        "result_content": "results",
        "result_files": "files",
        "next_steps": "nextSteps",
    }

    def to_dict(self):
        merged = {}
        if self.data:
            try:
                merged = json.loads(self.data)
            except (json.JSONDecodeError, TypeError):
                pass

        for col, key in self._COLUMN_MAP.items():
            val = getattr(self, col, "")
            if val:
                try:
                    merged[key] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass

        return {
            "id": self.id,
            "task_id": self.task_id,
            "role": self.role,
            "type": self.type,
            "content": self.content,
            "data": json.dumps(merged, ensure_ascii=False) if merged else "",
            "created_at": self.created_at.isoformat() + "+00:00" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "+00:00" if self.updated_at else None,
        }
