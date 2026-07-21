from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvaluationMetric(BaseModel):
    name: str
    score: float
    passed: bool


class EvaluationReport(BaseModel):
    name: str
    passed: bool
    metrics: list[EvaluationMetric]
    summary: str


class RetrievalEvaluationCase(BaseModel):
    """One labeled semantic-retrieval evaluation case."""

    query: str = Field(min_length=1, max_length=2000)
    expected_memory_id: int = Field(ge=1)

    @field_validator("query")
    @classmethod
    def reject_blank_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Query cannot be blank")
        return value


class RetrievalEvaluationRequest(BaseModel):
    """Bounded labeled dataset submitted to the retrieval evaluator."""

    cases: list[RetrievalEvaluationCase] = Field(min_length=1, max_length=100)
    limit: int = Field(default=5, ge=1, le=20)


class AgentFeedbackCreate(BaseModel):
    """Expert correction used to generate a targeted regression case."""

    workflow_id: int = Field(ge=1)
    correction: str = Field(min_length=3, max_length=4000)
    expected_outcome: str = Field(min_length=3, max_length=4000)


class AgentFeedbackRead(BaseModel):
    id: int
    workflow_id: int
    correction: str
    expected_outcome: str
    regression_case: dict[str, Any]
    suggested_task: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
