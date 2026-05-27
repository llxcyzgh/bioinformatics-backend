from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Template


class TemplateService:

    @staticmethod
    def get_all_templates(db: Session, user_id: int) -> List[Template]:
        """Get user's own templates and all public templates"""
        own = Template.where(db, user_id=user_id).all()
        public = db.query(Template).filter(
            Template.is_public == True,
            Template.deleted_at == 0,
            Template.user_id != user_id,
        ).all()
        return own + public

    @staticmethod
    def get_template_by_id(db: Session, template_id: int, user_id: int) -> Optional[Template]:
        """Get template by ID, must be owner or public"""
        template = Template.find(db, template_id)
        if template and (template.user_id == user_id or template.is_public):
            return template
        return None

    @staticmethod
    def create_template(db: Session, name: str, description: str | None, is_public: bool, scripts: str, user_id: int) -> Template:
        template = Template(
            name=name,
            description=description,
            is_public=is_public,
            scripts=scripts,
            user_id=user_id,
        )
        return template.save(db)

    @staticmethod
    def update_template(db: Session, template: Template, **kwargs) -> Template:
        for key, value in kwargs.items():
            if value is not None and hasattr(template, key):
                setattr(template, key, value)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def delete_template(db: Session, template: Template) -> None:
        template.delete(db)
