from typing import List

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services import TemplateService


class TemplateController:

    @staticmethod
    def index(db: Session, user_id: int) -> dict:
        templates = TemplateService.get_all_templates(db, user_id)
        return {"data": [t.to_dict() for t in templates]}

    @staticmethod
    def show(template_id: int, db: Session, user_id: int) -> JSONResponse:
        template = TemplateService.get_template_by_id(db, template_id, user_id)
        if not template:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Template not found"}
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=template.to_dict()
        )

    @staticmethod
    def store(name: str, description: str | None, is_public: bool, scripts: str, user_id: int, db: Session) -> JSONResponse:
        template = TemplateService.create_template(db, name, description, is_public, scripts, user_id)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=template.to_dict()
        )

    @staticmethod
    def update(template_id: int, db: Session, user_id: int, **kwargs) -> JSONResponse:
        template = TemplateService.get_template_by_id(db, template_id, user_id)
        if not template:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Template not found"}
            )

        # Only owner can update
        if template.user_id != user_id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Forbidden"}
            )

        TemplateService.update_template(db, template, **kwargs)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=template.to_dict()
        )

    @staticmethod
    def destroy(template_id: int, db: Session, user_id: int) -> JSONResponse:
        template = TemplateService.get_template_by_id(db, template_id, user_id)
        if not template:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Template not found"}
            )

        if template.user_id != user_id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Forbidden"}
            )

        TemplateService.delete_template(db, template)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Template deleted successfully"}
        )
