import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Project, Task


class TaskService:
    """Task service for business logic related to tasks"""

    @staticmethod
    def get_all_tasks(db: Session, user_id: int) -> List[Task]:
        """Get all tasks for a specific user"""
        return Task.where(db, user_id=user_id).all()

    @staticmethod
    def get_task_by_id(db: Session, task_id: int, user_id: int) -> Optional[Task]:
        """Get task by ID and user_id (ownership check)"""
        task = Task.find(db, task_id)
        if task and task.user_id == user_id:
            return task
        return None

    @staticmethod
    def create_task(
        db: Session,
        name: str,
        project_id: int,
        user_id: int,
    ) -> Task:
        """Create a new task, verifying project ownership"""
        project = Project.find(db, project_id)
        if not project or project.user_id != user_id:
            raise ValueError("Project not found")

        task = Task(
            uuid=str(uuid.uuid4()),
            name=name,
            project_id=project_id,
            user_id=user_id,
        )
        return task.save(db)

    @staticmethod
    def update_task(db: Session, task: Task, **kwargs) -> Task:
        """Update task fields"""
        for key, value in kwargs.items():
            if value is not None and hasattr(task, key):
                setattr(task, key, value)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task: Task) -> None:
        """Soft delete a task"""
        task.delete(db)
