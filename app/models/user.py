from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.models.model import Model


class User(Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)

    def __repr__(self):
        return f"<User {self.username}>"

    def to_dict(self):
        """User specific to_dict that hides password"""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
        }
