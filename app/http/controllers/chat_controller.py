import json
import logging

from fastapi import UploadFile
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services import ChatService
from app.services.upload_service import UploadService

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
        image_ids: list[int] | None = None,
        images: list[UploadFile] | None = None,
    ) -> JSONResponse:
        try:
            # Handle inline image uploads
            all_image_ids = list(image_ids) if image_ids else []

            if images:
                for img in images:
                    try:
                        record = UploadService.create(img, user_id, db, task_id or 0)
                        all_image_ids.append(record.id)
                    except ValueError as e:
                        logger.warning(f"[ChatController] 图片上传失败: {e}")

            image_filenames = [img.filename for img in images if img.filename] if images else None

            result = ChatService.chat(
                db=db,
                task_id=task_id,
                project_id=project_id,
                content=content,
                msg_type=msg_type,
                user_id=user_id,
                image_ids=all_image_ids if all_image_ids else None,
                image_filenames=image_filenames,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=result)
        except ValueError as e:
            code = status.HTTP_403_FORBIDDEN if str(e) == "Forbidden" else status.HTTP_404_NOT_FOUND
            return JSONResponse(status_code=code, content={"detail": str(e)})
