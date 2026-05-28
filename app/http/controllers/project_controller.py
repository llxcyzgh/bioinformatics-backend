from typing import List

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services import ProjectService


class ProjectController:
    """Project controller
    Similar to Laravel's ProjectController
    """

    @staticmethod
    def index(db: Session, user_id: int) -> List[dict]:
        """Get all projects for the current user"""
        projects = ProjectService.get_all_projects(db, user_id)
        return [project.to_dict() for project in projects]

    @staticmethod
    def show(project_id: int, db: Session, user_id: int) -> JSONResponse:
        """Get a specific project"""
        project = ProjectService.get_project_by_id(db, project_id, user_id)
        if not project:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Project not found"}
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=project.to_dict()
        )

    @staticmethod
    def store(
        name: str,
        description: str | None,
        user_id: int,
        db: Session,
    ) -> JSONResponse:
        """Create a new project"""
        project = ProjectService.create_project(db, name, description, user_id)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=project.to_dict()
        )

    @staticmethod
    def update(project_id: int, db: Session, user_id: int, **kwargs) -> JSONResponse:
        """Update a project"""
        project = ProjectService.get_project_by_id(db, project_id, user_id)
        if not project:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Project not found"}
            )

        ProjectService.update_project(db, project, **kwargs)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=project.to_dict()
        )

    @staticmethod
    def destroy(project_id: int, db: Session, user_id: int) -> JSONResponse:
        """Delete a project"""
        project = ProjectService.get_project_by_id(db, project_id, user_id)
        if not project:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Project not found"}
            )

        ProjectService.delete_project(db, project)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Project deleted successfully"}
        )

    @staticmethod
    def rename(project_id: int, name: str, db: Session, user_id: int) -> JSONResponse:
        """Rename a project"""
        project = ProjectService.get_project_by_id(db, project_id, user_id)
        if not project:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Project not found"}
            )
        try:
            project = ProjectService.rename_project(db, project, name)
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"detail": str(e)}
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=project.to_dict()
        )
