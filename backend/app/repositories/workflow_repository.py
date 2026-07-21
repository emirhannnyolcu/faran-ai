import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.workflow_run import WorkflowRun


class WorkflowRepository:
    """Database access for agent workflow runs."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        user_input: str,
        plan: list[str],
        max_attempts: int = 3,
        runtime: str = "deterministic",
        conversation_id: str | None = None,
        status: str = "pending",
    ) -> WorkflowRun:
        """Create a pending workflow run."""
        workflow = WorkflowRun(
            user_input=user_input,
            status=status,
            attempt_count=0,
            max_attempts=max_attempts,
            plan_json=json.dumps(plan),
            runtime=runtime,
            conversation_id=conversation_id,
        )
        self.db.add(workflow)
        self.db.flush()
        self.db.refresh(workflow)
        return workflow

    def latest_response_id(self, conversation_id: str) -> str | None:
        """Return the newest stored OpenAI response for a conversation."""
        workflow = (
            self.db.query(WorkflowRun)
            .filter(
                WorkflowRun.conversation_id == conversation_id,
                WorkflowRun.status == "completed",
                WorkflowRun.response_id.isnot(None),
            )
            .order_by(WorkflowRun.id.desc())
            .first()
        )
        return workflow.response_id if workflow is not None else None

    def get_by_id(self, workflow_id: int) -> WorkflowRun | None:
        """Return a workflow run by id."""
        return self.db.query(WorkflowRun).filter(WorkflowRun.id == workflow_id).first()

    def list_queued(self, limit: int = 10) -> list[WorkflowRun]:
        """Return oldest queued workflows for a bounded worker batch."""
        return (
            self.db.query(WorkflowRun)
            .filter(WorkflowRun.status == "queued")
            .order_by(WorkflowRun.id.asc())
            .limit(limit)
            .all()
        )

    def claim(self, workflow_id: int) -> bool:
        """Atomically claim one queued workflow for a single worker."""
        updated = (
            self.db.query(WorkflowRun)
            .filter(
                WorkflowRun.id == workflow_id,
                WorkflowRun.status == "queued",
            )
            .update(
                {
                    WorkflowRun.status: "claimed",
                    WorkflowRun.updated_at: datetime.now(UTC),
                },
                synchronize_session=False,
            )
        )
        return updated == 1

    def begin(self, workflow: WorkflowRun) -> WorkflowRun:
        """Mark a workflow attempt as running."""
        now = datetime.now(UTC)
        workflow.status = "running"
        workflow.attempt_count += 1
        workflow.last_error = None
        workflow.started_at = now
        workflow.completed_at = None
        workflow.updated_at = now
        self.db.flush()
        self.db.refresh(workflow)
        return workflow

    def complete(
        self,
        workflow: WorkflowRun,
        result: dict[str, Any],
        response_id: str | None = None,
    ) -> WorkflowRun:
        """Mark a workflow run as completed."""
        workflow.status = "completed"
        workflow.result_json = json.dumps(result)
        workflow.response_id = response_id
        workflow.last_error = None
        workflow.completed_at = datetime.now(UTC)
        workflow.updated_at = workflow.completed_at
        self.db.flush()
        self.db.refresh(workflow)
        return workflow

    def fail(self, workflow: WorkflowRun, error: str) -> WorkflowRun:
        """Mark a workflow run as failed."""
        workflow.status = "failed"
        workflow.result_json = None
        workflow.last_error = error
        workflow.updated_at = datetime.now(UTC)
        self.db.flush()
        self.db.refresh(workflow)
        return workflow
