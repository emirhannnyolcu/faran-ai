from types import SimpleNamespace
from datetime import UTC, datetime, timedelta

from app.ai.model_settings import build_agent_model_settings
from app.ai.providers import OpenAINoteAnalysisProvider
from app.core.settings import settings
from app.agents.openai_orchestrator import (
    _connected_workspace_tools,
    build_openai_agent_graph,
)
from app.services.schedule_service import ScheduleService
from app.services.workflow_service import execute_workflow


def test_gpt56_agent_settings_enable_reasoning_continuity_and_cache():
    model_settings = build_agent_model_settings()

    assert settings.OPENAI_MODEL == "gpt-5.6-sol"
    assert model_settings.reasoning is not None
    assert model_settings.reasoning.context == "all_turns"
    assert model_settings.reasoning.effort == settings.OPENAI_REASONING_EFFORT
    assert model_settings.store is True
    assert model_settings.prompt_cache_options == {
        "mode": settings.OPENAI_PROMPT_CACHE_MODE,
        "ttl": "30m",
    }
    assert model_settings.context_management == [
        {
            "type": "compaction",
            "compact_threshold": settings.OPENAI_CONTEXT_COMPACT_THRESHOLD,
        }
    ]


def test_openai_agent_graph_has_planner_root_and_workspace_handoff():
    graph = build_openai_agent_graph()

    assert graph.name == "Planner Agent"
    assert graph.model == settings.OPENAI_ANALYSIS_MODEL
    assert len(graph.handoffs) == 1
    assert graph.handoffs[0].agent_name == "FARAN Workspace Agent"


def test_openai_note_analysis_uses_luna_structured_output(monkeypatch):
    captured = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                output_text=(
                    '{"summary":"S","topic":"T","tags":["x"],'
                    '"importance":3,"ai_insights":"I"}'
                )
            )

    monkeypatch.setattr(
        OpenAINoteAnalysisProvider,
        "_get_client",
        lambda self: SimpleNamespace(responses=FakeResponses()),
    )

    result = OpenAINoteAnalysisProvider().analyze_note("A bounded note")

    assert '"summary":"S"' in result
    assert captured["model"] == settings.OPENAI_ANALYSIS_MODEL
    assert captured["text"]["format"]["type"] == "json_schema"
    assert captured["text"]["format"]["strict"] is True
    assert captured["reasoning"] == {
        "effort": "low",
        "context": "current_turn",
    }
    assert captured["store"] is False


def test_async_workflow_api_executes_and_exposes_status(client, monkeypatch):
    monkeypatch.setattr("app.api.agent.settings.AGENT_RUNTIME", "deterministic")

    response = client.post(
        "/agent/workflows",
        json={
            "user_input": "Create a focused weekly plan",
            "conversation_id": "build-week-demo",
        },
    )

    assert response.status_code == 202
    workflow_id = response.json()["workflow_id"]
    status_response = client.get(f"/agent/workflows/{workflow_id}")
    payload = status_response.json()
    assert status_response.status_code == 200
    assert payload["status"] == "completed"
    assert payload["conversation_id"] == "build-week-demo"
    assert payload["result"]["tasks"]
    assert payload["result"]["memory_id"] is not None


def test_openai_runtime_chains_conversation_response_ids(client, monkeypatch):
    calls = []

    async def fake_run(*args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            final_output="Grounded workspace result",
            new_items=[],
            last_response_id=f"resp-{len(calls)}",
        )

    monkeypatch.setattr("app.api.dependencies.settings.AGENT_RUNTIME", "openai")
    monkeypatch.setattr(
        "app.agents.openai_orchestrator.settings.OPENAI_API_KEY",
        "test-key",
    )
    monkeypatch.setattr("app.agents.openai_orchestrator.Runner.run", fake_run)

    first = client.post(
        "/agent/run",
        json={"user_input": "Start the goal", "conversation_id": "session-42"},
    )
    second = client.post(
        "/agent/run",
        json={"user_input": "Continue the goal", "conversation_id": "session-42"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["response_id"] == "resp-1"
    assert second.json()["response_id"] == "resp-2"
    assert calls[0]["previous_response_id"] is None
    assert calls[1]["previous_response_id"] == "resp-1"
    assert calls[1]["auto_previous_response_id"] is True


def test_demo_workspace_is_served(client):
    response = client.get("/demo")

    assert response.status_code == 200
    assert "<title>FARAN</title>" in response.text
    assert "Bugün neyi gerçekleştirmek istiyorsun?" in response.text
    assert "API anahtarı" not in response.text
    assert "Sistem durumu" not in response.text


def test_allowlisted_remote_mcp_tool_is_opt_in(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_MCP_SERVER_URL", "https://mcp.example.com")
    monkeypatch.setattr(settings, "OPENAI_MCP_ALLOWED_TOOLS", "search_docs,read_file")

    tools = _connected_workspace_tools()

    assert len(tools) == 1
    assert tools[0].tool_config["server_url"] == "https://mcp.example.com"
    assert tools[0].tool_config["allowed_tools"] == ["search_docs", "read_file"]
    assert tools[0].tool_config["allowed_callers"] == ["direct"]


def test_schedule_enqueues_and_executes_due_workflow(client, monkeypatch):
    monkeypatch.setattr("app.services.schedule_service.settings.AGENT_RUNTIME", "deterministic")
    run_at = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
    created = client.post(
        "/agent/schedules",
        json={
            "user_input": "Prepare the scheduled weekly review",
            "conversation_id": "scheduled-review",
            "run_at": run_at,
        },
    )

    assert created.status_code == 201
    db = client.app.state.testing_session_factory()
    try:
        workflow_ids = ScheduleService(db).enqueue_due()
        engine = db.get_bind()
    finally:
        db.close()
    assert len(workflow_ids) == 1
    execute_workflow(engine, workflow_ids[0])

    workflow = client.get(f"/agent/workflows/{workflow_ids[0]}").json()
    schedules = client.get("/agent/schedules").json()
    assert workflow["status"] == "completed"
    assert schedules[0]["enabled"] is False
    assert schedules[0]["last_workflow_id"] == workflow_ids[0]


def test_schedule_can_be_deleted(client):
    created = client.post(
        "/agent/schedules",
        json={
            "user_input": "Run a future reflection",
            "run_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        },
    ).json()

    response = client.delete(f"/agent/schedules/{created['id']}")

    assert response.status_code == 200
    assert client.get("/agent/schedules").json() == []
