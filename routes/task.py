from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.http.controllers import MessageController, TaskController
from app.http.middleware import Auth
from app.http.requests import CreateMessageRequest, CreateTaskRequest, UpdateTaskRequest
from app.models import User
from database import get_db

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_class=JSONResponse)
def index(current_user: User = Auth, db: Session = Depends(get_db)):
    """Get all tasks for the current user
    GET /api/tasks
    """
    return TaskController.index(db, current_user.id)


@router.get("/{task_id}", response_class=JSONResponse)
def show(task_id: int, current_user: User = Auth, db: Session = Depends(get_db)):
    """Get a specific task
    GET /api/tasks/{id}
    """
    return TaskController.show(task_id, db, current_user.id)


@router.post("/", response_class=JSONResponse)
def store(
    request: CreateTaskRequest,
    current_user: User = Auth,
    db: Session = Depends(get_db)
):
    """Create a new task
    POST /api/tasks
    """
    return TaskController.store(
        request.name,
        request.project_id,
        current_user.id,
        db
    )


@router.put("/{task_id}", response_class=JSONResponse)
def update(
    task_id: int,
    request: UpdateTaskRequest,
    current_user: User = Auth,
    db: Session = Depends(get_db)
):
    """Update a task
    PUT /api/tasks/{id}
    """
    return TaskController.update(
        task_id,
        db,
        current_user.id,
        name=request.name
    )


@router.delete("/{task_id}", response_class=JSONResponse)
def destroy(
    task_id: int,
    current_user: User = Auth,
    db: Session = Depends(get_db)
):
    """Delete a task
    DELETE /api/tasks/{id}
    """
    return TaskController.destroy(task_id, db, current_user.id)


# ---------------------------------------------------------------------------
# Nested Message routes under /tasks/{task_id}
# ---------------------------------------------------------------------------

@router.get("/{task_id}/messages", response_class=JSONResponse)
def messages_index(
    task_id: int,
    current_user: User = Auth,
    db: Session = Depends(get_db)
):
    """Get all messages for a task
    GET /api/tasks/{task_id}/messages
    """
    return MessageController.index(task_id, db, current_user.id)


@router.post("/{task_id}/messages", response_class=JSONResponse)
def messages_store(
    task_id: int,
    request: CreateMessageRequest,
    current_user: User = Auth,
    db: Session = Depends(get_db)
):
    """Create a user message and return the AI system response
    POST /api/tasks/{task_id}/messages
    """
    return MessageController.store(
        task_id,
        request.type,
        request.content,
        request.data,
        current_user.id,
        db
    )


@router.delete("/{task_id}/messages/{message_id}", response_class=JSONResponse)
def messages_destroy(
    task_id: int,
    message_id: int,
    current_user: User = Auth,
    db: Session = Depends(get_db)
):
    """Delete a message
    DELETE /api/tasks/{task_id}/messages/{message_id}
    """
    return MessageController.destroy(message_id, db, current_user.id)
