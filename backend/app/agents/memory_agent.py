from app.agents.base import AgentContext
from app.agents.tool_agent import ToolAgent


class MemoryAgent:
    """Gather relevant context and preserve a planned goal in long-term memory."""

    name = "Memory Agent"

    def __init__(self, tool_agent: ToolAgent) -> None:
        self.tool_agent = tool_agent

    def run(self, context: AgentContext) -> None:
        if context.goal_analysis is None or context.workflow_id is None:
            raise RuntimeError("Goal workflow context is incomplete")
        if not context.tasks:
            raise RuntimeError("Goal workflow does not contain tasks")

        retrieval = context.artifacts.get("research_retrieval")
        if retrieval is None:
            retrieval = self.tool_agent.call(
                context,
                "search_memory",
                query=context.user_input,
                limit=5,
            )
        assembled = context.artifacts.get("research_context")
        if assembled is None:
            assembled = self.tool_agent.call(
                context,
                "assemble_context",
                query=context.user_input,
                limit=5,
            )
        reflection = self.tool_agent.call(context, "reflect_memory")
        memory = self.tool_agent.call(
            context,
            "save_goal_memory",
            source_id=context.workflow_id,
            goal_analysis=context.goal_analysis.model_dump(),
            plan=context.plan,
            tasks=[task.model_dump() for task in context.tasks],
            research=context.research.model_dump() if context.research else None,
        )

        context.artifacts["retrieval"] = retrieval
        context.artifacts["context"] = assembled
        context.artifacts["reflection"] = reflection
        context.memory_id = memory.id
        context.record(
            self.name,
            "preserve_goal",
            (
                f"Retrieved {len(retrieval.results)} related memories and saved "
                f"goal workflow memory {memory.id}."
            ),
        )
