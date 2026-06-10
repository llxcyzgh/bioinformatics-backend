from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models.model import Model
from pkg.helpers.time_helper import get_utc_now


class Execution(Model):
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    deleted_at = Column(Integer, default=0, nullable=False)

    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, default=0)
    tool_ids = Column(Text, nullable=False, default='')
    script_content = Column(Text, nullable=False, default='')
    script_path = Column(String, nullable=False, default='')
    qsub_id = Column(String, nullable=False, default='')
    status = Column(String, nullable=False, default='pending')
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=False, default='')
    log_content = Column(Text, nullable=False, default='')

    task = relationship("Task", backref="executions")

    def __repr__(self):
        return f"<Execution {self.id} task={self.task_id} status={self.status}>"

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "tool_ids": self.tool_ids,
            "script_content": self.script_content,
            "script_path": self.script_path,
            "qsub_id": self.qsub_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() + "+00:00" if self.started_at else None,
            "finished_at": self.finished_at.isoformat() + "+00:00" if self.finished_at else None,
            "error_message": self.error_message,
            "log_content": self.log_content,
            "created_at": self.created_at.isoformat() + "+00:00" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "+00:00" if self.updated_at else None,
        }
