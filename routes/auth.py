from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.http.controllers import AuthController
from app.http.middleware import Auth
from app.http.requests import LoginRequest
from database import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint
    POST /api/auth/login
    """
    return AuthController.login(str(request.email), request.password, db)


@router.post("/logout")
def logout():
    """Logout endpoint
    POST /api/auth/logout
    """
    return AuthController.logout()


@router.get("/me")
def me(current_user: User = Auth):
    """Get current user
    GET /api/auth/me
    Requires authentication
    """
    return AuthController.me(current_user)
