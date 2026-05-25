from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import select

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models import User


class AuthService:
    """Authentication service, similar to Laravel's Auth facade"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[int]:
        """Verify a JWT token and return user ID"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            return int(user_id) if user_id else None
        except JWTError:
            return None

    @staticmethod
    def login(email: str, password: str, db: Session) -> tuple[Optional[dict], Optional[str]]:
        """
        Login a user and return token
        Returns (result_dict, None) on success, (None, error_message) on failure
        """
        stmt = select(User).where(User.email == email, User.deleted_at == 0)
        user = db.scalar(stmt)

        if not user:
            return None, "账号密码不正确"

        if not bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
            return None, "账号密码不匹配"

        access_token = AuthService.create_access_token(data={"sub": str(user.id)})
        return {
            "token": access_token,
            "user": user.to_dict(),
        }, None
