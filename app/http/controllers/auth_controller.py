from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services import AuthService


class AuthController:
    """Authentication controller
    Similar to Laravel's AuthController
    """

    @staticmethod
    def login(email: str, password: str, db: Session) -> JSONResponse:
        """Handle login request"""
        result, error = AuthService.login(email, password, db)

        if error:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": error}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result
        )

    @staticmethod
    def register(email: str, password: str, db: Session) -> JSONResponse:
        """Handle registration request"""
        result, error = AuthService.register(email, password, db)

        if error:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": error}
            )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=result
        )

    @staticmethod
    def logout():
        """Handle logout request"""
        # For JWT, logout is handled client-side by deleting token
        return {"message": "Logged out successfully"}

    @staticmethod
    def me(current_user) -> dict:
        """Get current authenticated user"""
        return {
            "id": current_user.id,
            "username": current_user.username,
            "realname": current_user.full_name,
            "email": current_user.email,
            "roles": [{"id": 1, "name": "admin", "description": "Administrator", "created_at": "", "updated_at": ""}] if current_user.username == "admin" else [{"id": 2, "name": "user", "description": "User", "created_at": "", "updated_at": ""}],
            "permissions": [{"id": 1, "name": "*", "description": "All permissions", "created_at": "", "updated_at": ""}] if current_user.username == "admin" else [],
        }

    @staticmethod
    def change_password(current_user, old_password: str, new_password: str, db: Session) -> JSONResponse:
        result, error = AuthService.change_password(current_user, old_password, new_password, db)

        if error:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": error}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result
        )
