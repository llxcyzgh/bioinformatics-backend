import logging
from sqlalchemy.orm import Session

from app.models import ScriptFolder

logger = logging.getLogger(__name__)


class ScriptFolderService:

    @staticmethod
    def list_all(db: Session) -> list[ScriptFolder]:
        return ScriptFolder.where(db).order_by(ScriptFolder.sort_order.asc()).all()

    @staticmethod
    def create(db: Session, name: str, parent_id: int = 0, sort_order: int = 0) -> ScriptFolder:
        folder = ScriptFolder(
            name=name,
            parent_id=parent_id,
            sort_order=sort_order,
        )
        return folder.save(db)

    @staticmethod
    def update(db: Session, folder_id: int, name: str = None, parent_id: int = None, sort_order: int = None) -> ScriptFolder:
        folder = ScriptFolder.find(db, folder_id)
        if not folder:
            raise ValueError("Folder not found")
        if name is not None:
            folder.name = name
        if parent_id is not None:
            folder.parent_id = parent_id
        if sort_order is not None:
            folder.sort_order = sort_order
        return folder.save(db)

    @staticmethod
    def delete(db: Session, folder_id: int) -> dict:
        folder = ScriptFolder.find(db, folder_id)
        if not folder:
            raise ValueError("Folder not found")
        folder.delete(db)
        return {"detail": "Deleted"}
