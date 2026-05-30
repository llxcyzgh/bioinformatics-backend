from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.http.controllers import ScriptFolderController
from app.http.middleware import Auth
from app.http.requests.script_request import CreateScriptFolderRequest, UpdateScriptFolderRequest
from app.models import User
from database import get_db

router = APIRouter(prefix="/script-folders", tags=["script-folders"])


@router.get("/")
def list_folders(db: Session = Depends(get_db)):
    return ScriptFolderController.list_all(db)


@router.post("/")
def create_folder(
    request: CreateScriptFolderRequest,
    current_user: User = Auth,
    db: Session = Depends(get_db),
):
    return ScriptFolderController.create(
        name=request.name,
        parent_id=request.parent_id,
        sort_order=request.sort_order,
        db=db,
    )


@router.put("/{folder_id}")
def update_folder(
    folder_id: int,
    request: UpdateScriptFolderRequest,
    current_user: User = Auth,
    db: Session = Depends(get_db),
):
    data = {k: v for k, v in request.model_dump().items() if v is not None}
    return ScriptFolderController.update(folder_id, db=db, **data)


@router.delete("/{folder_id}")
def delete_folder(
    folder_id: int,
    current_user: User = Auth,
    db: Session = Depends(get_db),
):
    return ScriptFolderController.delete(folder_id, db)
