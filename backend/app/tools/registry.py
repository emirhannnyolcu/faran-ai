from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


ToolHandler = Callable[..., Any]


@dataclass(frozen=True)
class ToolDefinition:
    """Application tool callable by an agent workflow."""

    name: str
    description: str
    handler: ToolHandler
    arguments_model: type[BaseModel] | None = None

    def openai_schema(self) -> dict[str, Any]:
        """Return this tool in the Responses API function-tool format."""
        parameters = (
            self.arguments_model.model_json_schema()
            if self.arguments_model is not None
            else {"type": "object", "properties": {}, "additionalProperties": False}
        )
        _make_json_schema_strict(parameters)
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": parameters,
            "strict": True,
        }


class ToolRegistry:
    """Registry for programmatic internal tool calling."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Register or replace a tool definition."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        """Return a tool by name."""
        return self._tools[name]

    def list_tools(self) -> list[ToolDefinition]:
        """Return all registered tools."""
        return list(self._tools.values())

    def openai_schemas(self) -> list[dict[str, Any]]:
        """Return model-facing schemas for every registered tool."""
        return [tool.openai_schema() for tool in self.list_tools()]

    def call(self, name: str, **kwargs: Any) -> Any:
        """Call a registered tool."""
        tool = self.get(name)
        if tool.arguments_model is None:
            return tool.handler(**kwargs)

        injected = {key: value for key, value in kwargs.items() if key == "db"}
        arguments = {key: value for key, value in kwargs.items() if key != "db"}
        validated = tool.arguments_model.model_validate(arguments)
        return tool.handler(**injected, **validated.model_dump())


def _make_json_schema_strict(schema: dict[str, Any]) -> None:
    """Apply Responses API strict-object requirements recursively."""
    if schema.get("type") == "object":
        schema["additionalProperties"] = False
        properties = schema.get("properties", {})
        schema["required"] = list(properties)
    for value in schema.values():
        if isinstance(value, dict):
            _make_json_schema_strict(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _make_json_schema_strict(item)
