from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Project


class ProjectService:
    """Project service for business logic related to projects"""

    @staticmethod
    def get_all_projects(db: Session, user_id: int) -> List[Project]:
        """Get all projects for a specific user"""
        return Project.where(db, user_id=user_id)

    @staticmethod
    def get_project_by_id(db: Session, project_id: int, user_id: int) -> Optional[Project]:
        """Get project by ID and user_id (ownership check)"""
        project = Project.find(db, project_id)
        if project and project.user_id == user_id:
            return project
        return None

    @staticmethod
    def create_project(
        db: Session,
        name: str,
        description: Optional[str],
        user_id: int,
    ) -> Project:
        """Create a new project"""
        project = Project(
            name=name,
            description=description,
            user_id=user_id,
        )
        return project.save(db)

    @staticmethod
    def update_project(db: Session, project: Project, **kwargs) -> Project:
        """Update project fields"""
        for key, value in kwargs.items():
            if value is not None and hasattr(project, key):
                setattr(project, key, value)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(db: Session, project: Project) -> None:
        """Soft delete a project"""
        project.delete(db)

    @staticmethod
    def rename_project(db: Session, project: Project, name: str) -> Project:
        """Rename a project, enforcing unique name"""
        existing = db.query(Project).filter(
            Project.name == name,
            Project.id != project.id,
            Project.deleted_at == 0,
        ).first()
        if existing:
            raise ValueError("Project name already exists")
        project.name = name
        db.commit()
        db.refresh(project)
        return project
