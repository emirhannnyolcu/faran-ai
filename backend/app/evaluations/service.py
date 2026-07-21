import json

from sqlalchemy.orm import Session

from app.models.agent_feedback import AgentFeedback
from app.repositories.agent_feedback_repository import AgentFeedbackRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.evaluation import (
    AgentFeedbackCreate,
    AgentFeedbackRead,
    EvaluationMetric,
    EvaluationReport,
    RetrievalEvaluationCase,
)
from app.services.memory_query_service import MemoryQueryService
from app.services.retrieval_service import SemanticRetrievalService
from app.services.errors import WorkflowNotFoundError


class EvaluationService:
    """Run lightweight product-quality checks for FARAN."""

    def __init__(
        self,
        memory_query_service: MemoryQueryService,
        retrieval_service: SemanticRetrievalService,
        db: Session,
    ) -> None:
        self.memory_query_service = memory_query_service
        self.retrieval_service = retrieval_service
        self.db = db
        self.workflow_repository = WorkflowRepository(db)
        self.feedback_repository = AgentFeedbackRepository(db)

    def run_smoke_evaluation(self) -> EvaluationReport:
        """Evaluate whether memory surfaces have enough signal to be useful."""
        memories = self.memory_query_service.list_memories()
        memory_count = len(memories)
        high_importance_count = len(
            [memory for memory in memories if memory.importance >= 4]
        )
        has_topics_count = len([memory for memory in memories if memory.topic])

        metrics = [
            EvaluationMetric(
                name="memory_presence",
                score=1.0 if memory_count > 0 else 0.0,
                passed=memory_count > 0,
            ),
            EvaluationMetric(
                name="high_importance_signal",
                score=high_importance_count / memory_count if memory_count else 0.0,
                passed=high_importance_count > 0,
            ),
            EvaluationMetric(
                name="topic_coverage",
                score=has_topics_count / memory_count if memory_count else 0.0,
                passed=has_topics_count == memory_count and memory_count > 0,
            ),
        ]

        passed = all(metric.passed for metric in metrics)
        return EvaluationReport(
            name="faran_memory_smoke_eval",
            passed=passed,
            metrics=metrics,
            summary=(
                "Memory layer has enough signal for agent workflows."
                if passed
                else "Memory layer needs more data before agent workflows are useful."
            ),
        )

    def run_retrieval_evaluation(
        self,
        cases: list[RetrievalEvaluationCase],
        limit: int = 5,
    ) -> EvaluationReport:
        """Measure retrieval hit rate and mean reciprocal rank on labeled cases."""
        hits = 0
        reciprocal_rank_total = 0.0
        for case in cases:
            response = self.retrieval_service.search(case.query, limit=limit)
            ranked_ids = [result.memory.id for result in response.results]
            if case.expected_memory_id not in ranked_ids:
                continue
            hits += 1
            rank = ranked_ids.index(case.expected_memory_id) + 1
            reciprocal_rank_total += 1.0 / rank

        case_count = len(cases)
        hit_rate = hits / case_count
        mean_reciprocal_rank = reciprocal_rank_total / case_count
        metrics = [
            EvaluationMetric(
                name=f"hit_rate_at_{limit}",
                score=round(hit_rate, 6),
                passed=hit_rate >= 0.8,
            ),
            EvaluationMetric(
                name="mean_reciprocal_rank",
                score=round(mean_reciprocal_rank, 6),
                passed=mean_reciprocal_rank >= 0.6,
            ),
        ]
        passed = all(metric.passed for metric in metrics)
        return EvaluationReport(
            name="faran_semantic_retrieval_eval",
            passed=passed,
            metrics=metrics,
            summary=(
                "Semantic retrieval meets the configured quality thresholds."
                if passed
                else "Semantic retrieval is below the configured quality thresholds."
            ),
        )

    def run_agent_evaluation(self, workflow_id: int) -> EvaluationReport:
        """Evaluate persisted workflow completion and output contracts."""
        workflow = self.workflow_repository.get_by_id(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError()
        result = json.loads(workflow.result_json) if workflow.result_json else {}
        tasks = result.get("tasks", []) if isinstance(result, dict) else []
        final_answer = result.get("final_answer") if isinstance(result, dict) else None
        memory_id = result.get("memory_id") if isinstance(result, dict) else None
        metrics = [
            EvaluationMetric(
                name="workflow_completed",
                score=1.0 if workflow.status == "completed" else 0.0,
                passed=workflow.status == "completed",
            ),
            EvaluationMetric(
                name="final_answer_present",
                score=1.0 if final_answer else 0.0,
                passed=bool(final_answer),
            ),
            EvaluationMetric(
                name="task_contract_present",
                score=1.0 if tasks else 0.0,
                passed=bool(tasks),
            ),
            EvaluationMetric(
                name="long_term_memory_persisted",
                score=1.0 if memory_id else 0.0,
                passed=bool(memory_id),
            ),
        ]
        passed = all(metric.passed for metric in metrics)
        return EvaluationReport(
            name="faran_agent_workflow_eval",
            passed=passed,
            metrics=metrics,
            summary=(
                "Agent workflow satisfies completion and persistence contracts."
                if passed
                else "Agent workflow is missing a required completion artifact."
            ),
        )

    def record_feedback(self, request: AgentFeedbackCreate) -> AgentFeedbackRead:
        """Convert an expert correction into a persisted targeted regression case."""
        workflow = self.workflow_repository.get_by_id(request.workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError()
        expected_terms = sorted(_significant_terms(request.expected_outcome))
        regression_case = {
            "workflow_id": request.workflow_id,
            "assertion": "expected_terms_present",
            "expected_terms": expected_terms,
            "minimum_coverage": 0.8,
        }
        feedback = self.feedback_repository.create(
            workflow_id=request.workflow_id,
            correction=request.correction,
            expected_outcome=request.expected_outcome,
            regression_case_json=json.dumps(regression_case),
            suggested_task=(
                "Update the bounded workflow behavior for correction "
                f"#{request.workflow_id}, then run its targeted regression case."
            ),
        )
        self.db.commit()
        return _feedback_read(feedback)

    def list_feedback(self, workflow_id: int) -> list[AgentFeedbackRead]:
        if self.workflow_repository.get_by_id(workflow_id) is None:
            raise WorkflowNotFoundError()
        return [
            _feedback_read(item)
            for item in self.feedback_repository.list_for_workflow(workflow_id)
        ]


def _significant_terms(text: str) -> set[str]:
    return {
        token.strip(".,!?;:").casefold()
        for token in text.split()
        if len(token.strip(".,!?;:")) >= 4
    }


def _feedback_read(feedback: AgentFeedback) -> AgentFeedbackRead:
    return AgentFeedbackRead(
        id=feedback.id,
        workflow_id=feedback.workflow_id,
        correction=feedback.correction,
        expected_outcome=feedback.expected_outcome,
        regression_case=json.loads(feedback.regression_case_json),
        suggested_task=feedback.suggested_task,
        status=feedback.status,
        created_at=feedback.created_at,
    )
