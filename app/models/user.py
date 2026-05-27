from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship

from app.models.model import Model
from pkg.helpers.time_helper import get_utc_now


class User(Model):
    __tablename__ = "users"

    # 显式定义这些字段以确保顺序 (会覆盖基类定义)
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    deleted_at = Column(Integer, default=0, nullable=False)

    # 业务字段
    email = Column(String, unique=True, index=True, nullable=False, default='')
    username = Column(String, index=True, nullable=False, default='')
    hashed_password = Column(String, nullable=False, default='')
    full_name = Column(String, nullable=False, default='')
    reset_password_signature = Column(String, nullable=False, default='')

    # 关系
    roles = relationship("Role", secondary="user_roles", backref="users")

    def __repr__(self):
        return f"<User {self.username}>"

    def to_dict(self):
        """User specific to_dict that hides password"""
        seen = set()
        permissions = []
        for role in self.roles:
            for perm in role.permissions:
                if perm.name not in seen:
                    seen.add(perm.name)
                    permissions.append(perm.to_dict())

        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "roles": [r.to_dict() for r in self.roles],
            "permissions": permissions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
