from datetime import datetime

from sqlalchemy.orm import Session

from app.models.workflow_schedule import WorkflowSchedule


class WorkflowScheduleRepository:
    """Database access for durable workflow schedules."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        user_input: str,
        runtime: str,
        next_run_at: datetime,
        interval_seconds: int | None,
        conversation_id: str | None,
    ) -> WorkflowSchedule:
        schedule = WorkflowSchedule(
            user_input=user_input,
            runtime=runtime,
            next_run_at=next_run_at,
            interval_seconds=interval_seconds,
            conversation_id=conversation_id,
        )
        self.db.add(schedule)
        self.db.flush()
        self.db.refresh(schedule)
        return schedule

    def get_by_id(self, schedule_id: int) -> WorkflowSchedule | None:
        return (
            self.db.query(WorkflowSchedule)
            .filter(WorkflowSchedule.id == schedule_id)
            .first()
        )

    def list_all(self) -> list[WorkflowSchedule]:
        return self.db.query(WorkflowSchedule).order_by(WorkflowSchedule.id).all()

    def list_due(self, now: datetime, limit: int = 10) -> list[WorkflowSchedule]:
        return (
            self.db.query(WorkflowSchedule)
            .filter(
                WorkflowSchedule.enabled.is_(True),
                WorkflowSchedule.next_run_at <= now,
            )
            .order_by(WorkflowSchedule.next_run_at, WorkflowSchedule.id)
            .limit(limit)
            .all()
        )

    def delete(self, schedule: WorkflowSchedule) -> None:
        self.db.delete(schedule)
        self.db.flush()
