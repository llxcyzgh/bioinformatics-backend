import json
import logging

from sqlalchemy.orm import Session

from app.models.execution import Execution
from app.models.task import Task
from pkg.helpers.time_helper import get_utc_now

logger = logging.getLogger(__name__)


class ExecutionService:

    @staticmethod
    def create(
        db: Session,
        task_id: int,
        tool_ids: list[str],
        script_content: str,
        script_path: str,
    ) -> Execution:
        record = Execution(
            task_id=task_id,
            tool_ids=json.dumps(tool_ids, ensure_ascii=False),
            script_content=script_content,
            script_path=script_path,
            status="pending",
        )
        return record.save(db)

    @staticmethod
    def start(db: Session, execution_id: int, qsub_id: str) -> Execution:
        record = Execution.find(db, execution_id)
        if not record:
            raise ValueError("Execution not found")
        record.qsub_id = qsub_id
        record.status = "running"
        record.started_at = get_utc_now()
        record.save(db)

        task = Task.find(db, record.task_id)
        if task:
            task.status = "running"
            task.save(db)

        return record

    @staticmethod
    def complete(db: Session, execution_id: int, log_content: str = "") -> Execution:
        record = Execution.find(db, execution_id)
        if not record:
            raise ValueError("Execution not found")
        record.status = "completed"
        record.finished_at = get_utc_now()
        record.log_content = log_content
        record.save(db)

        task = Task.find(db, record.task_id)
        if task:
            task.status = "completed"
            task.save(db)

        return record

    @staticmethod
    def fail(db: Session, execution_id: int, error_message: str, log_content: str = "") -> Execution:
        record = Execution.find(db, execution_id)
        if not record:
            raise ValueError("Execution not found")
        record.status = "failed"
        record.finished_at = get_utc_now()
        record.error_message = error_message
        record.log_content = log_content
        record.save(db)

        task = Task.find(db, record.task_id)
        if task:
            task.status = "failed"
            task.save(db)

        return record

    @staticmethod
    def cancel(db: Session, execution_id: int) -> Execution:
        record = Execution.find(db, execution_id)
        if not record:
            raise ValueError("Execution not found")
        record.status = "cancelled"
        record.finished_at = get_utc_now()
        record.save(db)

        task = Task.find(db, record.task_id)
        if task:
            task.status = "cancelled"
            task.save(db)

        return record

    @staticmethod
    def list_by_task(db: Session, task_id: int) -> list:
        return (
            db.query(Execution)
            .filter(Execution.task_id == task_id, Execution.deleted_at == 0)
            .order_by(Execution.id.desc())
            .all()
        )

    @staticmethod
    def get_latest(db: Session, task_id: int):
        return (
            db.query(Execution)
            .filter(Execution.task_id == task_id, Execution.deleted_at == 0)
            .order_by(Execution.id.desc())
            .first()
        )
