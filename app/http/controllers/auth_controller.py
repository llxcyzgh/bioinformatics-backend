from sqlalchemy.orm import Session

from app.services import AuthService
from database import get_db


class AuthController:
    """Authentication controller
    Similar to Laravel's AuthController
    """

    @staticmethod
    def login(email: str, password: str, db: Session) -> dict:
        """Handle login request"""
        return AuthService.login(email, password, db)

    @staticmethod
    def logout():
        """Handle logout request"""
        # For JWT, logout is handled client-side by deleting token
        return {"message": "Logged out successfully"}

    @staticmethod
    def me(current_user) -> dict:
        """Get current authenticated user"""
        return current_user.to_dict()
