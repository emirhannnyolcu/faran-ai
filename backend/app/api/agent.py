from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_agent_orchestrator,
    get_schedule_service,
    get_workflow_service,
)
from app.agents.orchestrator import AgentOrchestrator
from app.agents.openai_orchestrator import OpenAIAgentOrchestrator
from app.core.database import get_db
from app.core.settings import settings
from app.schemas.agent import (
    AgentRunRequest,
    AgentRunResponse,
    WorkflowScheduleCreate,
    WorkflowScheduleDeleteResponse,
    WorkflowScheduleRead,
    WorkflowStatusResponse,
)
from app.services.schedule_service import ScheduleService
from app.services.workflow_service import WorkflowService, execute_workflow


router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    request: AgentRunRequest,
    orchestrator: AgentOrchestrator | OpenAIAgentOrchestrator = Depends(
        get_agent_orchestrator
    ),
) -> AgentRunResponse:
    """Run FARAN's multi-agent workflow."""
    return await orchestrator.run(request.user_input, request.conversation_id)


@router.post("/workflows/{workflow_id}/retry", response_model=AgentRunResponse)
async def retry_agent_workflow(
    workflow_id: int,
    orchestrator: AgentOrchestrator | OpenAIAgentOrchestrator = Depends(
        get_agent_orchestrator
    ),
) -> AgentRunResponse:
    """Retry an eligible failed workflow run."""
    return await orchestrator.retry(workflow_id)


@router.post(
    "/workflows",
    response_model=WorkflowStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def enqueue_agent_workflow(
    request: AgentRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowStatusResponse:
    """Persist an API-triggered workflow and execute it outside the request path."""
    queued = service.enqueue(
        user_input=request.user_input,
        runtime=settings.AGENT_RUNTIME.lower(),
        conversation_id=request.conversation_id,
    )
    background_tasks.add_task(execute_workflow, db.get_bind(), queued.workflow_id)
    return queued


@router.get("/workflows/{workflow_id}", response_model=WorkflowStatusResponse)
def get_agent_workflow(
    workflow_id: int,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowStatusResponse:
    """Return durable progress and result state for an agent workflow."""
    return service.get_status(workflow_id)


@router.post("/schedules", response_model=WorkflowScheduleRead, status_code=201)
def create_workflow_schedule(
    request: WorkflowScheduleCreate,
    service: ScheduleService = Depends(get_schedule_service),
) -> WorkflowScheduleRead:
    """Create a one-time or recurring agent workflow trigger."""
    return service.create(request)


@router.get("/schedules", response_model=list[WorkflowScheduleRead])
def list_workflow_schedules(
    service: ScheduleService = Depends(get_schedule_service),
) -> list[WorkflowScheduleRead]:
    """List durable agent workflow schedules."""
    return service.list_all()


@router.delete(
    "/schedules/{schedule_id}",
    response_model=WorkflowScheduleDeleteResponse,
)
def delete_workflow_schedule(
    schedule_id: int,
    service: ScheduleService = Depends(get_schedule_service),
) -> WorkflowScheduleDeleteResponse:
    """Delete a workflow schedule."""
    service.delete(schedule_id)
    return WorkflowScheduleDeleteResponse(message="Workflow schedule deleted")
