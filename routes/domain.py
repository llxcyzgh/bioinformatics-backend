from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.http.controllers import DomainController
from app.http.middleware import RequireAdmin
from app.http.requests.domain_request import CreateDomainRequest, UpdateDomainRequest
from app.models import User, Domain
from database import get_db

router = APIRouter(prefix="/domains", tags=["domains"])


@router.get("/")
def list_domains(db: Session = Depends(get_db)):
    return DomainController.list_domains(db)


@router.get("/active")
def list_active_domains(db: Session = Depends(get_db)):
    """启用的领域（供路由分流/前端选择，登录用户可读）"""
    domains = Domain.where(db, is_active=1).order_by(Domain.sort_order.asc()).all()
    return {"data": [d.to_dict() for d in domains]}


@router.get("/{domain_id}")
def get_domain(domain_id: int, db: Session = Depends(get_db)):
    return DomainController.get_domain(domain_id, db)


@router.get("/{domain_id}/graph")
def get_domain_graph(domain_id: int, db: Session = Depends(get_db)):
    return DomainController.get_graph(domain_id, db)


@router.post("/{domain_id}/rebuild-graph")
def rebuild_domain_graph(
    domain_id: int,
    current_user: User = RequireAdmin,
    db: Session = Depends(get_db),
):
    """手动重建该领域的工具图（管理员）。"""
    return DomainController.rebuild_graph(domain_id, db)


@router.post("/")
def create_domain(
    req: CreateDomainRequest,
    current_user: User = RequireAdmin,
    db: Session = Depends(get_db),
):
    return DomainController.create_domain(db, req)


@router.put("/{domain_id}")
def update_domain(
    domain_id: int,
    req: UpdateDomainRequest,
    current_user: User = RequireAdmin,
    db: Session = Depends(get_db),
):
    return DomainController.update_domain(domain_id, db, req)


@router.patch("/{domain_id}/toggle")
def toggle_domain(
    domain_id: int,
    current_user: User = RequireAdmin,
    db: Session = Depends(get_db),
):
    return DomainController.toggle_domain(domain_id, db)


@router.delete("/{domain_id}")
def delete_domain(
    domain_id: int,
    current_user: User = RequireAdmin,
    db: Session = Depends(get_db),
):
    return DomainController.delete_domain(domain_id, db)
