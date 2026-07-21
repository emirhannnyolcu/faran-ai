from app.agents.base import AgentContext


class ReasoningAgent:
    """Reason over memory context and user intent."""

    name = "Reasoning Agent"

    def run(self, context: AgentContext) -> None:
        assembled = context.artifacts.get("context")
        reflection = context.artifacts.get("reflection")
        primary_count = len(assembled.primary_memories) if assembled else 0
        insight = reflection.insight if reflection else "No reflection available."
        reasoning = (
            f"Use {primary_count} primary memories. "
            f"Current reflection: {insight}"
        )
        context.artifacts["reasoning"] = reasoning
        context.record(self.name, "reason", reasoning)
