from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from app.models import User
from app.services import AuthService

security = HTTPBearer()


async def auth_middleware(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Authentication middleware
    Similar to Laravel's 'auth' middleware
    Verifies JWT token and injects current user
    """
    token = credentials.credentials
    user_id = AuthService.verify_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id, User.deleted_at == 0).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


# Alias for common use
Auth = Depends(auth_middleware)


async def require_admin(current_user: User = Depends(auth_middleware)) -> User:
    """要求当前用户具有 admin 角色"""
    if not any(r.name == "admin" for r in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user


# Admin-only dependency alias
RequireAdmin = Depends(require_admin)
