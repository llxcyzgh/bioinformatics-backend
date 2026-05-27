from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship

from app.models.model import Model
from pkg.helpers.time_helper import get_utc_now


class Role(Model):
    __tablename__ = "roles"

    # 显式定义这些字段以确保顺序 (会覆盖基类定义)
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    deleted_at = Column(Integer, default=0, nullable=False)

    # 业务字段
    name = Column(String, unique=True, index=True, nullable=False, default='')
    description = Column(String, nullable=True, default='')

    # 关系
    permissions = relationship("Permission", secondary="role_permissions", backref="roles")

    def __repr__(self):
        return f"<Role {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
