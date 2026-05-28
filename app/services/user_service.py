from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import User


class UserService:
    """User service for business logic related to users"""

    @staticmethod
    def get_all_users(db: Session) -> List[User]:
        """Get all users"""
        return db.query(User).order_by(User.id.desc()).all()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> User:
        """Create a new user"""
        from app.services.auth_service import AuthService

        # Check if email already exists
        if UserService.get_user_by_email(db, email):
            raise ValueError("Email already registered")

        # Check if username already exists
        if db.query(User).filter(User.username == username).first():
            raise ValueError("Username already taken")

        user = User(
            email=email,
            username=username,
            hashed_password=AuthService.hash_password(password),
            full_name=full_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
