from app.agents.base import AgentContext


class WriterAgent:
    """Write the final user-facing response."""

    name = "Writer Agent"

    def run(self, context: AgentContext) -> str:
        if context.goal_analysis is None:
            raise RuntimeError("Goal analysis is missing")

        research_summary = _research_summary(context)
        final_answer = (
            f"FARAN analyzed the goal '{context.goal_analysis.goal}', created "
            f"{len(context.tasks)} ordered tasks, {research_summary}, and saved "
            "the workflow to "
            f"long-term memory as item {context.memory_id}."
        )
        context.record(self.name, "write", "Generated final response.")
        return final_answer


def _research_summary(context: AgentContext) -> str:
    research = context.research
    if research is None or research.status == "skipped":
        return "did not require separate research"
    if research.status == "insufficient":
        return "identified missing research evidence"
    return f"used {len(research.findings)} relevant memory findings"
