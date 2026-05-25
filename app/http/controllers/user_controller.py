from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.services import UserService


class UserController:
    """User controller
    Similar to Laravel's UserController
    """

    @staticmethod
    def index(db: Session) -> List[dict]:
        """Get all users"""
        users = UserService.get_all_users(db)
        return [user.to_dict() for user in users]

    @staticmethod
    def show(user_id: int, db: Session) -> dict:
        """Get a specific user"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user.to_dict()

    @staticmethod
    def store(email: str, username: str, password: str, full_name: str | None, db: Session) -> dict:
        """Create a new user"""
        try:
            user = UserService.create_user(db, email, username, password, full_name)
            return user.to_dict()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    @staticmethod
    def update(user_id: int, db: Session, **kwargs) -> dict:
        """Update a user"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user.to_dict()

    @staticmethod
    def destroy(user_id: int, db: Session) -> dict:
        """Delete a user"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        db.delete(user)
        db.commit()
        return {"message": "User deleted successfully"}
