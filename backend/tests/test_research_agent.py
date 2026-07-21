from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from app.agents.base import AgentContext
from app.agents.planner_agent import PlannerAgent
from app.agents.research_agent import ResearchAgent
from app.agents.tool_agent import ToolAgent
from app.tools.registry import ToolRegistry


class StubToolAgent(ToolAgent):
    """Return deterministic memory tool results for Research Agent tests."""

    def __init__(self, *, with_findings: bool) -> None:
        self.with_findings = with_findings
        self.calls: list[str] = []

    def call(
        self,
        context: AgentContext,
        tool_name: str,
        **kwargs: Any,
    ) -> Any:
        self.calls.append(tool_name)
        if tool_name == "search_memory":
            results = []
            if self.with_findings:
                memory = SimpleNamespace(
                    id=7,
                    summary="A relevant saved learning strategy",
                    topic="Learning",
                )
                results.append(SimpleNamespace(memory=memory, score=0.91))
            return SimpleNamespace(results=results)
        if tool_name == "assemble_context":
            return SimpleNamespace(context_text="Grounded memory context")
        raise AssertionError(f"Unexpected tool call: {tool_name}")


def build_context(goal: str) -> AgentContext:
    context = AgentContext(
        user_input=goal,
        db=MagicMock(),
        tools=ToolRegistry(),
    )
    PlannerAgent().run(context)
    return context


def test_research_agent_skips_simple_goal_without_tool_calls():
    context = build_context("Build a weekly learning habit")
    tool_agent = StubToolAgent(with_findings=True)

    ResearchAgent(tool_agent).run(context)

    assert context.research is not None
    assert context.research.status == "skipped"
    assert context.research.decision.required is False
    assert tool_agent.calls == []


def test_research_agent_returns_structured_memory_findings():
    context = build_context("Compare learning strategies in my saved memory")
    tool_agent = StubToolAgent(with_findings=True)

    ResearchAgent(tool_agent).run(context)

    assert context.research is not None
    assert context.research.status == "completed"
    assert context.research.decision.required is True
    assert context.research.findings[0].memory_id == 7
    assert context.research.findings[0].relevance_score == 0.91
    assert context.research.context_text == "Grounded memory context"
    assert tool_agent.calls == ["search_memory", "assemble_context"]


def test_research_agent_reports_insufficient_memory_evidence():
    context = build_context("Research a new learning strategy")
    tool_agent = StubToolAgent(with_findings=False)

    ResearchAgent(tool_agent).run(context)

    assert context.research is not None
    assert context.research.status == "insufficient"
    assert context.research.findings == []
    assert tool_agent.calls == ["search_memory", "assemble_context"]


def test_research_decision_avoids_partial_word_false_positive():
    context = build_context("Organize resource allocation for the week")

    assert context.research_decision is not None
    assert context.research_decision.required is False


def test_research_decision_supports_turkish_word_forms():
    context = build_context("Kay\u0131tlar\u0131mdaki fikirleri kar\u015f\u0131la\u015ft\u0131r")

    assert context.research_decision is not None
    assert context.research_decision.required is True
