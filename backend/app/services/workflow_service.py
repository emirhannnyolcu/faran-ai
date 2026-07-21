import asyncio
import json
from typing import Any

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.agents.openai_orchestrator import OpenAIAgentOrchestrator
from app.agents.orchestrator import AgentOrchestrator
from app.core.logging import get_logger
from app.core.settings import settings
from app.models.workflow_run import WorkflowRun
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.agent import WorkflowStatusResponse
from app.services.errors import WorkflowNotFoundError


logger = get_logger(__name__)


class WorkflowService:
    """Queue and inspect durable agent workflow runs."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = WorkflowRepository(db)

    def enqueue(
        self,
        user_input: str,
        runtime: str,
        conversation_id: str | None = None,
    ) -> WorkflowStatusResponse:
        workflow = self.repository.create(
            user_input=user_input,
            plan=[],
            max_attempts=settings.WORKFLOW_MAX_ATTEMPTS,
            runtime=runtime,
            conversation_id=conversation_id,
            status="queued",
        )
        self.db.commit()
        return workflow_status(workflow)

    def get_status(self, workflow_id: int) -> WorkflowStatusResponse:
        workflow = self.repository.get_by_id(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError()
        return workflow_status(workflow)


def workflow_status(workflow: WorkflowRun) -> WorkflowStatusResponse:
    result: dict[str, Any] | None = None
    if workflow.result_json:
        parsed = json.loads(workflow.result_json)
        result = parsed if isinstance(parsed, dict) else {"value": parsed}
    return WorkflowStatusResponse(
        workflow_id=workflow.id,
        status=workflow.status,
        runtime=workflow.runtime,
        conversation_id=workflow.conversation_id,
        attempt_count=workflow.attempt_count,
        max_attempts=workflow.max_attempts,
        result=result,
        error=workflow.last_error,
    )


def execute_workflow(engine: Engine, workflow_id: int) -> None:
    """Claim and execute a queued workflow using an isolated DB session."""
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = factory()
    try:
        repository = WorkflowRepository(db)
        if not repository.claim(workflow_id):
            db.rollback()
            return
        db.commit()
        workflow = repository.get_by_id(workflow_id)
        if workflow is None:
            return
        orchestrator = _orchestrator_for_runtime(workflow.runtime, db)
        asyncio.run(orchestrator.execute_queued(workflow_id))
    except Exception:
        db.rollback()
        workflow = WorkflowRepository(db).get_by_id(workflow_id)
        if workflow is not None and workflow.status in {"queued", "claimed", "running"}:
            WorkflowRepository(db).fail(workflow, "Background workflow failed")
            db.commit()
        logger.exception("Background workflow %s failed", workflow_id)
    finally:
        db.close()


def _orchestrator_for_runtime(
    runtime: str,
    db: Session,
) -> AgentOrchestrator | OpenAIAgentOrchestrator:
    if runtime == "openai":
        return OpenAIAgentOrchestrator(db)
    return AgentOrchestrator(db)
