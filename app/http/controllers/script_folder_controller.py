from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services import ScriptFolderService


class ScriptFolderController:

    @staticmethod
    def list_all(db: Session) -> JSONResponse:
        folders = ScriptFolderService.list_all(db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"data": [f.to_dict() for f in folders]},
        )

    @staticmethod
    def create(name: str, parent_id: int, sort_order: int, db: Session) -> JSONResponse:
        folder = ScriptFolderService.create(db, name, parent_id, sort_order)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"data": folder.to_dict()},
        )

    @staticmethod
    def update(folder_id: int, db: Session, **kwargs) -> JSONResponse:
        try:
            folder = ScriptFolderService.update(db, folder_id, **kwargs)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data": folder.to_dict()},
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": str(e)},
            )

    @staticmethod
    def delete(folder_id: int, db: Session) -> JSONResponse:
        try:
            ScriptFolderService.delete(db, folder_id)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"detail": "Deleted"},
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": str(e)},
            )
