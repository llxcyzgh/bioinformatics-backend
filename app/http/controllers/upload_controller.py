import os

from fastapi import status
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from app.services.upload_service import UploadService


class UploadController:

    @staticmethod
    def upload(file, user_id: int, db, task_id: int = 0) -> JSONResponse:
        try:
            record = UploadService.create(file, user_id, db, task_id)
            return JSONResponse(status_code=status.HTTP_201_CREATED, content=record.to_dict())
        except ValueError as e:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(e)})

    @staticmethod
    def list_files(user_id: int, db, category: str = None, task_id: int = None) -> JSONResponse:
        records = UploadService.list_by_user(db, user_id, category, task_id)
        return JSONResponse(status_code=status.HTTP_200_OK, content=[r.to_dict() for r in records])

    @staticmethod
    def download(file_id: int, user_id: int, db) -> JSONResponse | FileResponse:
        record = UploadService.find(db, file_id, user_id)
        if not record:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "文件不存在"})
        file_path = UploadService.get_file_path(record)
        if not os.path.exists(file_path):
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "文件已丢失"})
        return FileResponse(
            file_path,
            filename=record.original_name,
            media_type=record.mime_type,
        )

    @staticmethod
    def delete(file_id: int, user_id: int, db) -> JSONResponse:
        record = UploadService.delete(db, file_id, user_id)
        if not record:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "文件不存在"})
        return JSONResponse(status_code=status.HTTP_200_OK, content={"detail": "已删除"})
