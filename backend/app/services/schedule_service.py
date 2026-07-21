from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.workflow_schedule import WorkflowSchedule
from app.repositories.workflow_repository import WorkflowRepository
from app.repositories.workflow_schedule_repository import WorkflowScheduleRepository
from app.schemas.agent import WorkflowScheduleCreate, WorkflowScheduleRead
from app.services.errors import WorkflowScheduleNotFoundError


class ScheduleService:
    """Manage scheduled triggers and convert due schedules into queued workflows."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = WorkflowScheduleRepository(db)
        self.workflow_repository = WorkflowRepository(db)

    def create(self, request: WorkflowScheduleCreate) -> WorkflowScheduleRead:
        run_at = _naive_utc(request.run_at)
        schedule = self.repository.create(
            user_input=request.user_input,
            runtime=settings.AGENT_RUNTIME.lower(),
            next_run_at=run_at,
            interval_seconds=request.interval_seconds,
            conversation_id=request.conversation_id,
        )
        self.db.commit()
        return _schedule_read(schedule)

    def list_all(self) -> list[WorkflowScheduleRead]:
        return [_schedule_read(item) for item in self.repository.list_all()]

    def delete(self, schedule_id: int) -> None:
        schedule = self.repository.get_by_id(schedule_id)
        if schedule is None:
            raise WorkflowScheduleNotFoundError()
        self.repository.delete(schedule)
        self.db.commit()

    def enqueue_due(self, limit: int = 10) -> list[int]:
        now = datetime.now(UTC).replace(tzinfo=None)
        workflow_ids: list[int] = []
        for schedule in self.repository.list_due(now=now, limit=limit):
            workflow = self.workflow_repository.create(
                user_input=schedule.user_input,
                plan=[],
                max_attempts=settings.WORKFLOW_MAX_ATTEMPTS,
                runtime=schedule.runtime,
                conversation_id=schedule.conversation_id,
                status="queued",
            )
            schedule.last_workflow_id = workflow.id
            schedule.updated_at = now
            if schedule.interval_seconds is None:
                schedule.enabled = False
            else:
                schedule.next_run_at = now + timedelta(
                    seconds=schedule.interval_seconds
                )
            workflow_ids.append(workflow.id)
        self.db.commit()
        return workflow_ids


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _schedule_read(schedule: WorkflowSchedule) -> WorkflowScheduleRead:
    return WorkflowScheduleRead(
        id=schedule.id,
        user_input=schedule.user_input,
        runtime=schedule.runtime,
        conversation_id=schedule.conversation_id,
        next_run_at=schedule.next_run_at,
        interval_seconds=schedule.interval_seconds,
        enabled=schedule.enabled,
        last_workflow_id=schedule.last_workflow_id,
    )
