from sqlalchemy import Column, String, Integer, DateTime, Text

from app.models.model import Model
from pkg.helpers.time_helper import get_utc_now


class Domain(Model):
    """领域 / 脚本库：一类分析（如扩增子、RNA-Seq），每个领域拥有独立的类型词表与工具图。"""
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    deleted_at = Column(Integer, default=0, nullable=False)

    name = Column(String, nullable=False, default='')
    code = Column(String, nullable=False, default='')
    description = Column(Text, nullable=False, default='')
    is_active = Column(Integer, nullable=False, default=1)
    keywords = Column(String, nullable=False, default='')
    script_root = Column(String, nullable=False, default='uploaded')
    sort_order = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<Domain {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "is_active": self.is_active,
            "keywords": self.keywords,
            "script_root": self.script_root,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
