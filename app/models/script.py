from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models.model import Model
from pkg.helpers.time_helper import get_utc_now


class Script(Model):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    deleted_at = Column(Integer, default=0, nullable=False)

    name = Column(String, nullable=False, default='')
    description = Column(Text, nullable=False, default='')
    folder_id = Column(Integer, ForeignKey("script_folders.id"), nullable=False, default=0)
    tool_id = Column(String, nullable=False, default='')
    category = Column(String, nullable=False, default='')
    version = Column(String, nullable=False, default='1.0.0')
    file_path = Column(String, nullable=False, default='')
    md_content = Column(Text, nullable=False, default='')
    inputs = Column(Text, nullable=False, default='')
    outputs = Column(Text, nullable=False, default='')
    runtime = Column(Integer, nullable=False, default=0)
    cost = Column(Float, nullable=False, default=0.0)
    weight = Column(Integer, nullable=False, default=0)
    verified = Column(Integer, nullable=False, default=0)
    # 默认未启用：新上传脚本需先人工校验(verified=1)后才能启用(is_active=1)，启用后方进入建图
    is_active = Column(Integer, nullable=False, default=0)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, default=0)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=False, default=0)
    valid_from = Column(String, nullable=False, default='')
    valid_until = Column(String, nullable=False, default='')
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False, default=0)
    call_params = Column(Text, nullable=False, default='')
    call_outputs = Column(Text, nullable=False, default='')
    per_sample = Column(Integer, nullable=False, default=0)

    uploader = relationship("User", foreign_keys=[uploaded_by], backref="uploaded_scripts")
    verifier = relationship("User", foreign_keys=[verified_by])

    def __repr__(self):
        return f"<Script {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "folder_id": self.folder_id,
            "tool_id": self.tool_id,
            "category": self.category,
            "version": self.version,
            "file_path": self.file_path,
            "md_content": self.md_content,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "runtime": self.runtime,
            "cost": self.cost,
            "weight": self.weight,
            "verified": self.verified,
            "is_active": self.is_active,
            "uploaded_by": self.uploaded_by,
            "verified_by": self.verified_by,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "domain_id": self.domain_id,
            "call_params": self.call_params,
            "call_outputs": self.call_outputs,
            "per_sample": self.per_sample,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
