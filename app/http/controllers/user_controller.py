from typing import List

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

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
    def show(user_id: int, db: Session) -> JSONResponse:
        """Get a specific user"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "User not found"}
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=user.to_dict()
        )

    @staticmethod
    def store(email: str, username: str, password: str, full_name: str | None, db: Session) -> JSONResponse:
        """Create a new user"""
        try:
            user = UserService.create_user(db, email, username, password, full_name)
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=user.to_dict()
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": str(e)}
            )

    @staticmethod
    def update(user_id: int, db: Session, **kwargs) -> JSONResponse:
        """Update a user"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "User not found"}
            )

        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=user.to_dict()
        )

    @staticmethod
    def destroy(user_id: int, db: Session) -> JSONResponse:
        """Delete a user"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "User not found"}
            )

        user.delete(db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "User deleted successfully"}
        )
