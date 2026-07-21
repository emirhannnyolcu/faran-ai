from app.agents.base import AgentContext
from app.agents.tool_agent import ToolAgent
from app.schemas.agent import ResearchFinding, ResearchResult


class ResearchAgent:
    """Ground a goal in relevant long-term memory when research is required."""

    name = "Research Agent"

    def __init__(self, tool_agent: ToolAgent) -> None:
        self.tool_agent = tool_agent

    def run(self, context: AgentContext) -> None:
        decision = context.research_decision
        if decision is None:
            raise RuntimeError("Research decision is missing")

        if not decision.required:
            context.research = ResearchResult(
                decision=decision,
                status="skipped",
            )
            context.record(
                self.name,
                "research_skipped",
                "The goal does not require a separate research stage.",
            )
            return

        retrieval = self.tool_agent.call(
            context,
            "search_memory",
            query=decision.query,
            limit=5,
        )
        assembled = self.tool_agent.call(
            context,
            "assemble_context",
            query=decision.query,
            limit=5,
        )
        findings = [
            ResearchFinding(
                memory_id=result.memory.id,
                summary=result.memory.summary,
                topic=result.memory.topic,
                relevance_score=result.score,
            )
            for result in retrieval.results
        ]
        status = "completed" if findings else "insufficient"
        context.research = ResearchResult(
            decision=decision,
            status=status,
            findings=findings,
            context_text=assembled.context_text,
        )
        context.artifacts["research_retrieval"] = retrieval
        context.artifacts["research_context"] = assembled
        context.record(
            self.name,
            "research_memory",
            f"Research finished with {len(findings)} relevant memory findings.",
        )
