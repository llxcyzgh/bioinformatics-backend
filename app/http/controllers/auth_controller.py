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
    def logout():
        """Handle logout request"""
        # For JWT, logout is handled client-side by deleting token
        return {"message": "Logged out successfully"}

    @staticmethod
    def me(current_user) -> dict:
        """Get current authenticated user"""
        return current_user.to_dict()
