from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services.domain_service import DomainService


class DomainController:

    @staticmethod
    def list_domains(db: Session) -> JSONResponse:
        domains = DomainService.list_all(db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"data": [d.to_dict() for d in domains]},
        )

    @staticmethod
    def get_domain(domain_id: int, db: Session) -> JSONResponse:
        try:
            domain = DomainService.get(db, domain_id)
            return JSONResponse(status_code=status.HTTP_200_OK, content={"data": domain.to_dict()})
        except ValueError as e:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(e)})

    @staticmethod
    def create_domain(db: Session, req) -> JSONResponse:
        try:
            domain = DomainService.create_domain(db, req)
            return JSONResponse(status_code=status.HTTP_201_CREATED, content={"data": domain.to_dict()})
        except ValueError as e:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(e)})

    @staticmethod
    def update_domain(domain_id: int, db: Session, req) -> JSONResponse:
        try:
            domain = DomainService.update_domain(db, domain_id, req)
            return JSONResponse(status_code=status.HTTP_200_OK, content={"data": domain.to_dict()})
        except ValueError as e:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(e)})

    @staticmethod
    def toggle_domain(domain_id: int, db: Session) -> JSONResponse:
        try:
            domain = DomainService.toggle_active(db, domain_id)
            return JSONResponse(status_code=status.HTTP_200_OK, content={"data": domain.to_dict()})
        except ValueError as e:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(e)})

    @staticmethod
    def delete_domain(domain_id: int, db: Session) -> JSONResponse:
        try:
            DomainService.delete_domain(db, domain_id)
            return JSONResponse(status_code=status.HTTP_200_OK, content={"detail": "Deleted"})
        except ValueError as e:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(e)})

    @staticmethod
    def get_graph(domain_id: int, db: Session) -> JSONResponse:
        try:
            DomainService.get(db, domain_id)  # 404 if missing
            graph = DomainService.get_graph(db, domain_id)
            return JSONResponse(status_code=status.HTTP_200_OK, content={"data": graph})
        except ValueError as e:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(e)})

    @staticmethod
    def rebuild_graph(domain_id: int, db: Session) -> JSONResponse:
        """手动重建工具图：清缓存后重新推导，返回节点/边数。"""
        try:
            DomainService.get(db, domain_id)  # 404 if missing
            DomainService.invalidate(domain_id)
            graph = DomainService.get_graph(db, domain_id)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "data": {
                        "nodes": len(graph.get("nodes", [])),
                        "edges": len(graph.get("edges", [])),
                    }
                },
            )
        except ValueError as e:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(e)})
