from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship

from app.models.model import Model
from pkg.helpers.time_helper import get_utc_now


class ScriptFolder(Model):
    __tablename__ = "script_folders"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    deleted_at = Column(Integer, default=0, nullable=False)

    name = Column(String, nullable=False, default='')
    parent_id = Column(Integer, nullable=False, default=0)
    sort_order = Column(Integer, nullable=False, default=0)

    scripts = relationship("Script", backref="folder")

    def __repr__(self):
        return f"<ScriptFolder {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
