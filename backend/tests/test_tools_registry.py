import pytest
from pydantic import BaseModel, Field, ValidationError

from app.tools.registry import ToolDefinition, ToolRegistry


class EchoArguments(BaseModel):
    value: str = Field(min_length=1)


def test_tool_registry_registers_and_calls_tools():
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="echo",
            description="Echo a value.",
            handler=lambda value: value,
            arguments_model=EchoArguments,
        )
    )

    assert registry.call("echo", value="hello") == "hello"
    assert registry.list_tools()[0].name == "echo"

    schema = registry.openai_schemas()[0]
    assert schema["type"] == "function"
    assert schema["name"] == "echo"
    assert schema["strict"] is True
    assert schema["parameters"]["properties"]["value"]["type"] == "string"
    assert schema["parameters"]["additionalProperties"] is False

    with pytest.raises(ValidationError):
        registry.call("echo", value="")
