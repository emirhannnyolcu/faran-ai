from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class AgentRunRequest(BaseModel):
    user_input: str = Field(..., min_length=1, max_length=4000)
    conversation_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )

    @field_validator("user_input")
    @classmethod
    def reject_blank_input(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Input cannot be blank")
        return value


class AgentStep(BaseModel):
    agent: str
    action: str
    output: str


class GoalAnalysis(BaseModel):
    """Structured interpretation of a user goal."""

    goal: str
    objective: str
    topic: str
    success_criteria: list[str] = Field(min_length=1, max_length=5)


class PlannedTask(BaseModel):
    """One actionable task produced from a goal plan."""

    sequence: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=1000)
    status: Literal["pending"] = "pending"


class ResearchDecision(BaseModel):
    """Planner decision describing whether memory research is required."""

    required: bool
    reason: str = Field(min_length=1, max_length=500)
    query: str = Field(min_length=1, max_length=2000)


class ResearchFinding(BaseModel):
    """One relevant long-term memory selected by the Research Agent."""

    memory_id: int = Field(ge=1)
    summary: str
    topic: str
    relevance_score: float


class ResearchResult(BaseModel):
    """Structured outcome of the conditional research stage."""

    decision: ResearchDecision
    status: Literal["skipped", "completed", "insufficient"]
    findings: list[ResearchFinding] = Field(default_factory=list)
    context_text: str = ""


class OpenAIWorkflowOutput(BaseModel):
    """Strict final contract produced by the OpenAI Workspace Agent."""

    final_answer: str = Field(min_length=1, max_length=12000)
    tasks: list[str] = Field(min_length=1, max_length=20)
    research_status: Literal["skipped", "completed", "insufficient"]
    research_summary: str = Field(min_length=1, max_length=2000)
    completion_criteria: list[str] = Field(min_length=1, max_length=10)


class AgentRunResponse(BaseModel):
    workflow_id: int
    status: str
    plan: list[str]
    steps: list[AgentStep]
    final_answer: str
    goal_analysis: GoalAnalysis | None = None
    research: ResearchResult | None = None
    tasks: list[PlannedTask] = Field(default_factory=list)
    memory_id: int | None = None
    conversation_id: str | None = None
    response_id: str | None = None


class WorkflowStatusResponse(BaseModel):
    """Durable status returned for asynchronous agent workflows."""

    workflow_id: int
    status: Literal["queued", "claimed", "running", "completed", "failed"]
    runtime: Literal["deterministic", "openai"]
    conversation_id: str | None = None
    attempt_count: int
    max_attempts: int
    result: dict[str, Any] | None = None
    error: str | None = None


class WorkflowScheduleCreate(AgentRunRequest):
    """Create a one-time or recurring durable workflow schedule."""

    run_at: datetime
    interval_seconds: int | None = Field(default=None, ge=60, le=31_536_000)


class WorkflowScheduleRead(BaseModel):
    id: int
    user_input: str
    runtime: str
    conversation_id: str | None = None
    next_run_at: datetime
    interval_seconds: int | None = None
    enabled: bool
    last_workflow_id: int | None = None


class WorkflowScheduleDeleteResponse(BaseModel):
    message: str
