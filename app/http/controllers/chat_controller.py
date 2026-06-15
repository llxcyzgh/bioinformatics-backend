import logging

from fastapi import UploadFile
from fastapi import status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.services import ChatService

logger = logging.getLogger(__name__)


class ChatController:

    @staticmethod
    def chat(
        project_id: int,
        content: str,
        msg_type: str,
        user_id: int,
        db: Session,
        task_id: int | None = None,
        task_uuid: str | None = None,
        image_ids: list[int] | None = None,
        images: list[UploadFile] | None = None,
    ) -> JSONResponse:
        try:
            image_filenames = [img.filename for img in images if img.filename] if images else None

            result = ChatService.chat(
                db=db,
                task_id=task_id,
                task_uuid=task_uuid,
                project_id=project_id,
                content=content,
                msg_type=msg_type,
                user_id=user_id,
                image_ids=image_ids,
                images=images,
                image_filenames=image_filenames,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=result)
        except ValueError as e:
            code = status.HTTP_403_FORBIDDEN if str(e) == "Forbidden" else status.HTTP_404_NOT_FOUND
            return JSONResponse(status_code=code, content={"detail": str(e)})

    @staticmethod
    def confirm_path(
        task_uuid: str,
        project_id: int,
        candidate_id: str,
        candidate_data: str,
        user_id: int,
        db: Session,
    ) -> JSONResponse:
        try:
            result = ChatService.confirm_path(
                db=db,
                task_uuid=task_uuid,
                project_id=project_id,
                candidate_id=candidate_id,
                candidate_data=candidate_data,
                user_id=user_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=result)
        except ValueError as e:
            msg = str(e)
            if msg == "Forbidden":
                code = status.HTTP_403_FORBIDDEN
            elif "not found" in msg.lower():
                code = status.HTTP_404_NOT_FOUND
            else:
                code = status.HTTP_400_BAD_REQUEST
            return JSONResponse(status_code=code, content={"detail": msg})

    @staticmethod
    def confirm_upload(
        task_uuid: str,
        project_id: int,
        file_mappings: list[dict],
        user_id: int,
        db: Session,
        primer_f: str = "",
        primer_r: str = "",
    ) -> JSONResponse:
        try:
            result = ChatService.confirm_upload(
                db=db,
                task_uuid=task_uuid,
                project_id=project_id,
                file_mappings=file_mappings,
                user_id=user_id,
                primer_f=primer_f,
                primer_r=primer_r,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=result)
        except ValueError as e:
            msg = str(e)
            if msg == "Forbidden":
                code = status.HTTP_403_FORBIDDEN
            elif "not found" in msg.lower():
                code = status.HTTP_404_NOT_FOUND
            else:
                code = status.HTTP_400_BAD_REQUEST
            return JSONResponse(status_code=code, content={"detail": msg})

    @staticmethod
    def start_execution(
        task_uuid: str,
        project_id: int,
        user_id: int,
        db: Session,
    ) -> JSONResponse:
        try:
            result = ChatService.start_execution(
                db=db,
                task_uuid=task_uuid,
                project_id=project_id,
                user_id=user_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=result)
        except ValueError as e:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(e)})

    @staticmethod
    def simulate_execution(
        task_uuid: str,
        project_id: int,
        user_id: int,
        db: Session,
    ) -> JSONResponse:
        try:
            result = ChatService.simulate_execution(
                db=db,
                task_uuid=task_uuid,
                project_id=project_id,
                user_id=user_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=result)
        except ValueError as e:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(e)})

    @staticmethod
    def get_execution_logs(
        task_uuid: str,
        user_id: int,
        db: Session,
    ) -> JSONResponse:
        try:
            result = ChatService.get_execution_logs(
                db=db,
                task_uuid=task_uuid,
                user_id=user_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=result)
        except ValueError as e:
            msg = str(e)
            code = status.HTTP_404_NOT_FOUND if "not found" in msg.lower() else status.HTTP_400_BAD_REQUEST
            return JSONResponse(status_code=code, content={"detail": msg})

    @staticmethod
    def download_execution_logs(
        task_uuid: str,
        user_id: int,
        db: Session,
    ) -> FileResponse | JSONResponse:
        try:
            file_path, filename = ChatService.download_execution_logs(
                db=db,
                task_uuid=task_uuid,
                user_id=user_id,
            )
            return FileResponse(
                file_path,
                filename=filename,
                media_type="text/plain",
            )
        except ValueError as e:
            msg = str(e)
            code = status.HTTP_404_NOT_FOUND if "不存在" in msg or "not found" in msg.lower() else status.HTTP_400_BAD_REQUEST
            return JSONResponse(status_code=code, content={"detail": msg})

    @staticmethod
    def retry_execution(
        task_uuid: str,
        project_id: int,
        user_id: int,
        db: Session,
    ) -> JSONResponse:
        try:
            result = ChatService.retry_execution(
                db=db,
                task_uuid=task_uuid,
                project_id=project_id,
                user_id=user_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=result)
        except ValueError as e:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(e)})

    @staticmethod
    def reupload_and_execute(
        task_uuid: str,
        project_id: int,
        file_mappings: list[dict],
        user_id: int,
        db: Session,
        primer_f: str = "",
        primer_r: str = "",
    ) -> JSONResponse:
        try:
            result = ChatService.reupload_and_execute(
                db=db,
                task_uuid=task_uuid,
                project_id=project_id,
                file_mappings=file_mappings,
                user_id=user_id,
                primer_f=primer_f,
                primer_r=primer_r,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=result)
        except ValueError as e:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(e)})
