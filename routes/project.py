from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.http.controllers import ProjectController
from app.http.middleware import Auth
from app.http.requests import CreateProjectRequest, UpdateProjectRequest, RenameProjectRequest
from app.models import User
from database import get_db

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_class=JSONResponse)
def index(current_user: User = Auth, db: Session = Depends(get_db)):
    """Get all projects for the current user
    GET /api/projects
    """
    return ProjectController.index(db, current_user.id)


@router.get("/{project_id}", response_class=JSONResponse)
def show(project_id: int, current_user: User = Auth, db: Session = Depends(get_db)):
    """Get a specific project
    GET /api/projects/{id}
    """
    return ProjectController.show(project_id, db, current_user.id)


@router.post("/", response_class=JSONResponse)
def store(
    request: CreateProjectRequest,
    current_user: User = Auth,
    db: Session = Depends(get_db)
):
    """Create a new project
    POST /api/projects
    """
    return ProjectController.store(
        request.name,
        request.description,
        current_user.id,
        db
    )


@router.put("/{project_id}", response_class=JSONResponse)
def update(
    project_id: int,
    request: UpdateProjectRequest,
    current_user: User = Auth,
    db: Session = Depends(get_db)
):
    """Update a project
    PUT /api/projects/{id}
    """
    return ProjectController.update(
        project_id,
        db,
        current_user.id,
        name=request.name,
        description=request.description
    )


@router.delete("/{project_id}", response_class=JSONResponse)
def destroy(
    project_id: int,
    current_user: User = Auth,
    db: Session = Depends(get_db)
):
    """Delete a project
    DELETE /api/projects/{id}
    """
    return ProjectController.destroy(project_id, db, current_user.id)


@router.patch("/{project_id}/rename", response_class=JSONResponse)
def rename(
    project_id: int,
    request: RenameProjectRequest,
    current_user: User = Auth,
    db: Session = Depends(get_db)
):
    """Rename a project
    PATCH /api/projects/{id}/rename
    """
    return ProjectController.rename(project_id, request.name, db, current_user.id)
