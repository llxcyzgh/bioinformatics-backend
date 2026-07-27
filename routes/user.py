from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.http.controllers import UserController
from app.http.middleware import RequireAdmin
from app.http.requests import CreateUserRequest, UpdateUserRequest
from app.models import User
from database import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_class=JSONResponse)
def index(current_user: User = RequireAdmin, db: Session = Depends(get_db)):
    """Get all users
    GET /api/users
    Requires admin
    """
    return UserController.index(db)


@router.get("/{user_id}", response_class=JSONResponse)
def show(user_id: int, current_user: User = RequireAdmin, db: Session = Depends(get_db)):
    """Get a specific user
    GET /api/users/{id}
    Requires admin
    """
    return UserController.show(user_id, db)


@router.post("/", response_class=JSONResponse)
def store(request: CreateUserRequest, current_user: User = RequireAdmin, db: Session = Depends(get_db)):
    """Create a new user
    POST /api/users
    Requires admin
    """
    return UserController.store(
        str(request.email),
        request.username,
        request.password,
        request.full_name,
        db
    )


@router.put("/{user_id}", response_class=JSONResponse)
def update(user_id: int, request: UpdateUserRequest, current_user: User = RequireAdmin, db: Session = Depends(get_db)):
    """Update a user
    PUT /api/users/{id}
    Requires admin
    """
    return UserController.update(
        user_id,
        db,
        email=request.email,
        username=request.username,
        full_name=request.full_name
    )


@router.delete("/{user_id}", response_class=JSONResponse)
def destroy(user_id: int, current_user: User = RequireAdmin, db: Session = Depends(get_db)):
    """Delete a user
    DELETE /api/users/{id}
    Requires admin
    """
    return UserController.destroy(user_id, db)
