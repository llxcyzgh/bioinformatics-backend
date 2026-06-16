from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.http.controllers import ScriptController
from app.http.middleware import Auth
from app.models import User
from database import get_db

router = APIRouter(prefix="/scripts", tags=["scripts"])


@router.get("/")
def list_scripts(
    folder_id: Optional[int] = None,
    verified: Optional[int] = None,
    is_active: Optional[int] = None,
    tool_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return ScriptController.list_scripts(
        db, folder_id=folder_id, verified=verified, is_active=is_active, tool_id=tool_id
    )


@router.get("/{script_id}")
def get_script(script_id: int, db: Session = Depends(get_db)):
    return ScriptController.get_script(script_id, db)


@router.post("/")
def upload_script(
    script_file: UploadFile = File(...),
    md_file: Optional[UploadFile] = File(None),
    name: str = Form(...),
    folder_id: int = Form(0),
    tool_id: str = Form(""),
    category: str = Form(""),
    version: str = Form("1.0.0"),
    runtime: int = Form(0),
    cost: float = Form(0.0),
    weight: int = Form(0),
    inputs: str = Form("[]"),
    outputs: str = Form("[]"),
    valid_from: str = Form(""),
    valid_until: str = Form(""),
    current_user: User = Auth,
    db: Session = Depends(get_db),
):
    return ScriptController.upload_script(
        db=db,
        script_file=script_file,
        md_file=md_file,
        name=name,
        folder_id=folder_id,
        tool_id=tool_id,
        category=category,
        uploaded_by=current_user.id,
        version=version,
        runtime=runtime,
        cost=cost,
        weight=weight,
        inputs=inputs,
        outputs=outputs,
        valid_from=valid_from,
        valid_until=valid_until,
    )


@router.post("/bulk")
def upload_scripts_bulk(
    script_files: list[UploadFile] = File(...),
    folder_id: int = Form(0),
    domain_id: int = Form(0),
    version: str = Form("1.0.0"),
    runtime: int = Form(0),
    cost: float = Form(0.0),
    weight: int = Form(0),
    valid_from: str = Form(""),
    valid_until: str = Form(""),
    current_user: User = Auth,
    db: Session = Depends(get_db),
):
    return ScriptController.upload_scripts_bulk(
        db=db,
        script_files=script_files,
        folder_id=folder_id,
        domain_id=domain_id,
        uploaded_by=current_user.id,
        version=version,
        runtime=runtime,
        cost=cost,
        weight=weight,
        valid_from=valid_from,
        valid_until=valid_until,
    )


@router.post("/upload-library")
def upload_library(
    files: list[UploadFile] = File(...),
    paths: list[str] = Form(...),
    domain_id: int = Form(0),
    current_user: User = Auth,
    db: Session = Depends(get_db),
):
    """文件夹上传：files 与 paths 同序（paths 为浏览器相对路径），后端按基名配对 .sh+.md。"""
    return ScriptController.upload_library(
        db=db, files=files, paths=paths, domain_id=domain_id, uploaded_by=current_user.id
    )


@router.put("/{script_id}")
def update_script(
    script_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    folder_id: Optional[int] = Form(None),
    tool_id: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    version: Optional[str] = Form(None),
    runtime: Optional[int] = Form(None),
    cost: Optional[float] = Form(None),
    weight: Optional[int] = Form(None),
    inputs: Optional[str] = Form(None),
    outputs: Optional[str] = Form(None),
    valid_from: Optional[str] = Form(None),
    valid_until: Optional[str] = Form(None),
    current_user: User = Auth,
    db: Session = Depends(get_db),
):
    data = {}
    if name is not None: data["name"] = name
    if description is not None: data["description"] = description
    if folder_id is not None: data["folder_id"] = folder_id
    if tool_id is not None: data["tool_id"] = tool_id
    if category is not None: data["category"] = category
    if version is not None: data["version"] = version
    if runtime is not None: data["runtime"] = runtime
    if cost is not None: data["cost"] = cost
    if weight is not None: data["weight"] = weight
    if inputs is not None: data["inputs"] = inputs
    if outputs is not None: data["outputs"] = outputs
    if valid_from is not None: data["valid_from"] = valid_from
    if valid_until is not None: data["valid_until"] = valid_until
    return ScriptController.update_script(script_id, db=db, **data)


@router.patch("/{script_id}/verify")
def verify_script(
    script_id: int,
    current_user: User = Auth,
    db: Session = Depends(get_db),
):
    return ScriptController.verify_script(script_id, current_user.id, db)


@router.patch("/{script_id}/toggle")
def toggle_active(
    script_id: int,
    current_user: User = Auth,
    db: Session = Depends(get_db),
):
    return ScriptController.toggle_active(script_id, db)


@router.delete("/{script_id}")
def delete_script(
    script_id: int,
    current_user: User = Auth,
    db: Session = Depends(get_db),
):
    return ScriptController.delete_script(script_id, db)


@router.get("/{script_id}/download")
def download_script(script_id: int, db: Session = Depends(get_db)):
    return ScriptController.download_script(script_id, db)


@router.get("/{script_id}/source")
def get_script_source(script_id: int, db: Session = Depends(get_db)):
    """返回脚本真正的 .sh 源码文本（预览用，只读）。"""
    return ScriptController.get_source(script_id, db)
