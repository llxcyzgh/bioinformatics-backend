from typing import List

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services import TaskService


class TaskController:
    """Task controller
    Similar to Laravel's TaskController
    """

    @staticmethod
    def index(db: Session, user_id: int) -> List[dict]:
        """Get all tasks for the current user"""
        tasks = TaskService.get_all_tasks(db, user_id)
        return [task.to_dict() for task in tasks]

    @staticmethod
    def show(task_id: int, db: Session, user_id: int) -> JSONResponse:
        """Get a specific task"""
        task = TaskService.get_task_by_id(db, task_id, user_id)
        if not task:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Task not found"}
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=task.to_dict()
        )

    @staticmethod
    def store(
        name: str,
        project_id: int,
        user_id: int,
        db: Session,
    ) -> JSONResponse:
        """Create a new task"""
        try:
            task = TaskService.create_task(db, name, project_id, user_id)
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=task.to_dict()
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": str(e)}
            )

    @staticmethod
    def update(task_id: int, db: Session, user_id: int, **kwargs) -> JSONResponse:
        """Update a task"""
        task = TaskService.get_task_by_id(db, task_id, user_id)
        if not task:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Task not found"}
            )

        TaskService.update_task(db, task, **kwargs)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=task.to_dict()
        )

    @staticmethod
    def destroy(task_id: int, db: Session, user_id: int) -> JSONResponse:
        """Delete a task"""
        task = TaskService.get_task_by_id(db, task_id, user_id)
        if not task:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Task not found"}
            )

        TaskService.delete_task(db, task)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Task deleted successfully"}
        )
