from app.agents.base import AgentContext
from app.schemas.agent import PlannedTask


class TaskAgent:
    """Convert a planner output into ordered actionable tasks."""

    name = "Task Agent"

    def run(self, context: AgentContext) -> None:
        """Create one task per plan step and integrate research when available."""
        research_step = _research_plan_step(context)
        if research_step is not None:
            context.plan.insert(2, research_step)
        context.tasks = [
            PlannedTask(
                sequence=index,
                title=_task_title(step),
                description=step,
            )
            for index, step in enumerate(context.plan, start=1)
        ]
        context.record(
            self.name,
            "create_tasks",
            f"Created {len(context.tasks)} ordered tasks from the goal plan.",
        )


def _task_title(step: str) -> str:
    """Derive a concise task title without changing the plan meaning."""
    title = step.rstrip(".").strip()
    return title[:160]


def _research_plan_step(context: AgentContext) -> str | None:
    research = context.research
    if research is None or research.status == "skipped":
        return None
    if research.status == "insufficient":
        return "Collect the missing evidence required to validate the goal plan."

    summaries = "; ".join(finding.summary for finding in research.findings[:2])
    return f"Apply relevant long-term memory evidence to the plan: {summaries}"[:1000]
