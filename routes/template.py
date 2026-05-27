from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.http.controllers import TemplateController
from app.http.middleware import Auth
from app.http.requests import CreateTemplateRequest, UpdateTemplateRequest
from app.models import User
from database import get_db

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/", response_class=JSONResponse)
def index(current_user: User = Auth, db: Session = Depends(get_db)):
    return TemplateController.index(db, current_user.id)


@router.get("/{template_id}", response_class=JSONResponse)
def show(template_id: int, current_user: User = Auth, db: Session = Depends(get_db)):
    return TemplateController.show(template_id, db, current_user.id)


@router.post("/", response_class=JSONResponse)
def store(request: CreateTemplateRequest, current_user: User = Auth, db: Session = Depends(get_db)):
    return TemplateController.store(
        request.name,
        request.description,
        request.is_public,
        request.scripts,
        current_user.id,
        db
    )


@router.put("/{template_id}", response_class=JSONResponse)
def update(template_id: int, request: UpdateTemplateRequest, current_user: User = Auth, db: Session = Depends(get_db)):
    return TemplateController.update(
        template_id,
        db,
        current_user.id,
        name=request.name,
        description=request.description,
        is_public=request.is_public,
        scripts=request.scripts
    )


@router.delete("/{template_id}", response_class=JSONResponse)
def destroy(template_id: int, current_user: User = Auth, db: Session = Depends(get_db)):
    return TemplateController.destroy(template_id, db, current_user.id)
