from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.http.controllers import UserController
from app.http.middleware import Auth
from app.http.requests import CreateUserRequest, UpdateUserRequest
from database import get_db
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
def index(db: Session = Depends(get_db)):
    """Get all users
    GET /api/users
    Requires authentication
    """
    return UserController.index(db)


@router.get("/{user_id}")
def show(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user
    GET /api/users/{id}
    """
    return UserController.show(user_id, db)


@router.post("/")
def store(request: CreateUserRequest, db: Session = Depends(get_db)):
    """Create a new user
    POST /api/users
    """
    return UserController.store(
        str(request.email),
        request.username,
        request.password,
        request.full_name,
        db
    )


@router.put("/{user_id}")
def update(user_id: int, request: UpdateUserRequest, db: Session = Depends(get_db)):
    """Update a user
    PUT /api/users/{id}
    """
    return UserController.update(
        user_id,
        db,
        email=request.email,
        username=request.username,
        full_name=request.full_name
    )


@router.delete("/{user_id}")
def destroy(user_id: int, db: Session = Depends(get_db)):
    """Delete a user
    DELETE /api/users/{id}
    """
    return UserController.destroy(user_id, db)
