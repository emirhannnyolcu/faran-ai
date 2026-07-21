import re

from app.agents.base import AgentContext
from app.schemas.agent import GoalAnalysis, ResearchDecision


_RESEARCH_PREFIXES = (
    "ara\u015ft\u0131r",
    "kar\u015f\u0131la\u015ft\u0131r",
    "karsilastir",
    "de\u011ferlendir",
    "degerlendir",
    "investigat",
    "evaluat",
)
_RESEARCH_TERMS = (
    "kan\u0131t",
    "kanit",
    "kaynak",
    "alternatif",
    "incele",
    "research",
    "compare",
    "comparison",
    "evidence",
    "source",
    "sources",
    "alternative",
    "alternatives",
    "benchmark",
)


class PlannerAgent:
    """Create a compact execution plan for a user request."""

    name = "Planner Agent"

    def run(self, context: AgentContext) -> None:
        goal = context.user_input.strip()
        topic = _goal_topic(goal)
        context.goal_analysis = GoalAnalysis(
            goal=goal,
            objective=f"Turn the goal into an executable and reviewable outcome: {goal}",
            topic=topic,
            success_criteria=[
                "The desired outcome is explicit.",
                "The work is divided into ordered actionable tasks.",
                "Progress can be reviewed against the original goal.",
            ],
        )
        context.research_decision = _research_decision(goal)
        context.plan = [
            f"Define the concrete outcome for {topic}.",
            "Identify constraints, dependencies, and available context.",
            "Prepare the smallest useful first action.",
            "Execute the remaining work in a measurable order.",
            "Review the result and preserve the workflow in long-term memory.",
        ]
        context.record(
            self.name,
            "analyze_goal",
            (
                f"Analyzed the goal, created a {len(context.plan)}-step plan, "
                f"and marked research as "
                f"{'required' if context.research_decision.required else 'optional'}."
            ),
        )


def _goal_topic(goal: str) -> str:
    """Create a compact deterministic topic label from a goal."""
    words = goal.rstrip(".!?").split()
    topic = " ".join(words[:6]).strip()
    return topic[:120] or "Personal Goal"


def _research_decision(goal: str) -> ResearchDecision:
    """Choose research when the goal explicitly requires evidence or comparison."""
    normalized_goal = goal.casefold()
    matched_marker = _matched_research_marker(normalized_goal)
    if matched_marker is not None:
        reason = (
            "The goal asks for investigation, comparison, evaluation, or "
            f"supporting evidence (matched '{matched_marker}')."
        )
        required = True
    else:
        reason = "The goal can be planned without a separate research stage."
        required = False
    return ResearchDecision(required=required, reason=reason, query=goal)


def _matched_research_marker(normalized_goal: str) -> str | None:
    """Return a research marker without matching unrelated partial words."""
    tokens = re.findall(r"\w+", normalized_goal)
    exact_match = next((term for term in _RESEARCH_TERMS if term in tokens), None)
    if exact_match is not None:
        return exact_match
    return next(
        (
            prefix
            for prefix in _RESEARCH_PREFIXES
            if any(token.startswith(prefix) for token in tokens)
        ),
        None,
    )
