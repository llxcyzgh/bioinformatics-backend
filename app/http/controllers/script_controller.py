import os

from fastapi import UploadFile, status
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from app.services import ScriptService
from app.models import ScriptFolder
from config.upload import UPLOAD_DIR

SCRIPTS_DIR = os.getenv("SCRIPTS_DIR", "scripts")


def _resolve_category(db: Session, folder_id: int) -> str:
    """从 folder_id 推导 category：取直接上级文件夹名称"""
    folder = ScriptFolder.find(db, folder_id)
    return folder.name if folder else ""


class ScriptController:

    @staticmethod
    def list_scripts(db: Session, folder_id=None, verified=None, is_active=None, tool_id=None) -> JSONResponse:
        scripts = ScriptService.list_scripts(db, folder_id=folder_id, verified=verified, is_active=is_active, tool_id=tool_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"data": [s.to_dict() for s in scripts]},
        )

    @staticmethod
    def get_script(script_id: int, db: Session) -> JSONResponse:
        try:
            script = ScriptService.get(db, script_id)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data": script.to_dict()},
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": str(e)},
            )

    @staticmethod
    def upload_script(
        db: Session,
        script_file: UploadFile,
        md_file: UploadFile | None,
        name: str,
        folder_id: int,
        tool_id: str,
        category: str,
        uploaded_by: int,
        version: str,
        runtime: int,
        cost: float,
        weight: int,
        inputs: str,
        outputs: str,
        valid_from: str,
        valid_until: str,
    ) -> JSONResponse:
        try:
            category = _resolve_category(db, folder_id) or category
            script = ScriptService.upload_script(
                db=db,
                script_file=script_file,
                md_file=md_file,
                name=name,
                folder_id=folder_id,
                tool_id=tool_id,
                category=category,
                uploaded_by=uploaded_by,
                version=version,
                runtime=runtime,
                cost=cost,
                weight=weight,
                inputs=inputs,
                outputs=outputs,
                valid_from=valid_from,
                valid_until=valid_until,
            )
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data": script.to_dict()},
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": str(e)},
            )

    @staticmethod
    def upload_scripts_bulk(db: Session, script_files, folder_id: int, domain_id: int, uploaded_by: int, version: str, runtime: int, cost: float, weight: int, valid_from: str, valid_until: str) -> JSONResponse:
        try:
            scripts = ScriptService.upload_scripts_bulk(
                db=db,
                script_files=script_files,
                folder_id=folder_id,
                domain_id=domain_id,
                uploaded_by=uploaded_by,
                version=version,
                runtime=runtime,
                cost=cost,
                weight=weight,
                valid_from=valid_from,
                valid_until=valid_until,
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={"data": [s.to_dict() for s in scripts], "count": len(scripts)},
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": str(e)},
            )

    @staticmethod
    def upload_library(db: Session, files, paths, domain_id: int, uploaded_by: int) -> JSONResponse:
        try:
            result = ScriptService.upload_library(
                db=db, files=files, paths=paths, domain_id=domain_id, uploaded_by=uploaded_by
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "data": [s.to_dict() for s in result["created"]],
                    "warnings": result["warnings"],
                    "count": len(result["created"]),
                },
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": str(e)},
            )

    @staticmethod
    def update_script(script_id: int, db: Session, **kwargs) -> JSONResponse:
        try:
            if "folder_id" in kwargs:
                kwargs["category"] = _resolve_category(db, kwargs["folder_id"]) or kwargs.get("category", "")
            script = ScriptService.update(db, script_id, **kwargs)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data": script.to_dict()},
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": str(e)},
            )

    @staticmethod
    def verify_script(script_id: int, verified_by: int, db: Session) -> JSONResponse:
        try:
            script = ScriptService.verify(db, script_id, verified_by)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data": script.to_dict()},
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": str(e)},
            )

    @staticmethod
    def toggle_active(script_id: int, db: Session) -> JSONResponse:
        try:
            script = ScriptService.toggle_active(db, script_id)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"data": script.to_dict()},
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": str(e)},
            )

    @staticmethod
    def delete_script(script_id: int, db: Session) -> JSONResponse:
        try:
            ScriptService.delete(db, script_id)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"detail": "Deleted"},
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": str(e)},
            )

    @staticmethod
    def download_script(script_id: int, db: Session) -> FileResponse | JSONResponse:
        try:
            script = ScriptService.get(db, script_id)
            full_path = os.path.join(SCRIPTS_DIR, script.file_path)
            if not os.path.exists(full_path):
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"detail": "File not found on disk"},
                )
            filename = os.path.basename(script.file_path)
            return FileResponse(
                path=full_path,
                filename=f"{script.name}{os.path.splitext(script.file_path)[1]}",
                media_type="application/octet-stream",
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": str(e)},
            )
