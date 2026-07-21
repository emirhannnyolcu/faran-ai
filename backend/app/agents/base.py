from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.schemas.agent import (
    AgentStep,
    GoalAnalysis,
    PlannedTask,
    ResearchDecision,
    ResearchResult,
)
from app.tools.registry import ToolRegistry


@dataclass
class AgentContext:
    """Shared context passed between FARAN agents."""

    user_input: str
    db: Session
    tools: ToolRegistry
    workflow_id: int | None = None
    goal_analysis: GoalAnalysis | None = None
    research_decision: ResearchDecision | None = None
    research: ResearchResult | None = None
    plan: list[str] = field(default_factory=list)
    tasks: list[PlannedTask] = field(default_factory=list)
    memory_id: int | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)
    steps: list[AgentStep] = field(default_factory=list)

    def record(self, agent: str, action: str, output: str) -> None:
        """Record an agent step."""
        self.steps.append(AgentStep(agent=agent, action=action, output=output))
