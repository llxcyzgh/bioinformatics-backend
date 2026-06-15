from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey

from app.models.model import Model
from pkg.helpers.time_helper import get_utc_now


class DataType(Model):
    """领域级数据类型词表：type_id 在领域内唯一；is_uploadable=1 表示用户需上传的根输入。"""
    __tablename__ = "data_types"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    deleted_at = Column(Integer, default=0, nullable=False)

    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False, default=0)
    type_id = Column(String, nullable=False, default='')
    label = Column(String, nullable=False, default='')
    description = Column(Text, nullable=False, default='')
    extensions = Column(Text, nullable=False, default='')
    required = Column(Integer, nullable=False, default=1)
    multiple = Column(Integer, nullable=False, default=0)
    is_uploadable = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<DataType {self.domain_id}:{self.type_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "domain_id": self.domain_id,
            "type_id": self.type_id,
            "label": self.label,
            "description": self.description,
            "extensions": self.extensions,
            "required": self.required,
            "multiple": self.multiple,
            "is_uploadable": self.is_uploadable,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
