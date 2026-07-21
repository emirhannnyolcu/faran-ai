from typing import Any

from app.agents.base import AgentContext


class ToolAgent:
    """Execute internal FARAN tools for other agents."""

    name = "Tool Agent"

    def call(
        self,
        context: AgentContext,
        tool_name: str,
        **kwargs: Any,
    ) -> Any:
        result = context.tools.call(tool_name, db=context.db, **kwargs)
        context.record(self.name, f"tool:{tool_name}", "Tool executed successfully.")
        return result
