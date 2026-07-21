from fastapi import APIRouter, Depends

from app.api.dependencies import get_evaluation_service
from app.evaluations.service import EvaluationService
from app.schemas.evaluation import (
    AgentFeedbackCreate,
    AgentFeedbackRead,
    EvaluationReport,
    RetrievalEvaluationRequest,
)


router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


@router.get("/smoke", response_model=EvaluationReport)
def run_smoke_evaluation(
    service: EvaluationService = Depends(get_evaluation_service),
) -> EvaluationReport:
    """Run FARAN's lightweight smoke evaluation."""
    return service.run_smoke_evaluation()


@router.post("/retrieval", response_model=EvaluationReport)
def run_retrieval_evaluation(
    request: RetrievalEvaluationRequest,
    service: EvaluationService = Depends(get_evaluation_service),
) -> EvaluationReport:
    """Evaluate semantic retrieval against a labeled dataset."""
    return service.run_retrieval_evaluation(request.cases, limit=request.limit)


@router.get("/agent/{workflow_id}", response_model=EvaluationReport)
def run_agent_evaluation(
    workflow_id: int,
    service: EvaluationService = Depends(get_evaluation_service),
) -> EvaluationReport:
    """Evaluate one persisted agent workflow against product contracts."""
    return service.run_agent_evaluation(workflow_id)


@router.post("/feedback", response_model=AgentFeedbackRead, status_code=201)
def record_agent_feedback(
    request: AgentFeedbackCreate,
    service: EvaluationService = Depends(get_evaluation_service),
) -> AgentFeedbackRead:
    """Turn an expert correction into a targeted regression case."""
    return service.record_feedback(request)


@router.get(
    "/agent/{workflow_id}/feedback",
    response_model=list[AgentFeedbackRead],
)
def list_agent_feedback(
    workflow_id: int,
    service: EvaluationService = Depends(get_evaluation_service),
) -> list[AgentFeedbackRead]:
    """List targeted regression cases generated for a workflow."""
    return service.list_feedback(workflow_id)
