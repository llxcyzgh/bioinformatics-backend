from sqlalchemy import Column, Integer, DateTime, ForeignKey

from app.models.model import Model
from pkg.helpers.time_helper import get_utc_now


class RolePermission(Model):
    __tablename__ = "role_permissions"

    # 显式定义这些字段以确保顺序 (会覆盖基类定义)
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    deleted_at = Column(Integer, default=0, nullable=False)

    # 业务字段
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, default=0)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False, default=0)

    def __repr__(self):
        return f"<RolePermission role={self.role_id} perm={self.permission_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "role_id": self.role_id,
            "permission_id": self.permission_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
