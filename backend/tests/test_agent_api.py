from types import SimpleNamespace

import app.services.note_service as note_service_module
from app.models.workflow_run import WorkflowRun
from app.schemas.ai import NoteAnalysis


def fake_analyze_note(content: str) -> NoteAnalysis:
    return NoteAnalysis(
        summary=f"Agent memory for {content}",
        topic="Agentic Workflow",
        tags=["agent", "memory"],
        importance=5,
        ai_insights="This memory should support agent execution.",
    )


def test_agent_run_executes_workflow_and_persists_state(client, monkeypatch):
    monkeypatch.setattr(note_service_module, "analyze_note", fake_analyze_note)
    client.post(
        "/notes/",
        json={"title": "Agent memory", "content": "Plan with memory"},
    )

    response = client.post(
        "/agent/run",
        json={"user_input": "Help me plan with my memory"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["workflow_id"] == 1
    assert len(payload["plan"]) == 5
    assert "FARAN analyzed the goal" in payload["final_answer"]
    assert payload["goal_analysis"]["goal"] == "Help me plan with my memory"
    assert payload["research"]["status"] == "skipped"
    assert len(payload["tasks"]) == 5
    assert payload["memory_id"] == 2
    assert {step["agent"] for step in payload["steps"]} >= {
        "Planner Agent",
        "Task Agent",
        "Tool Agent",
        "Memory Agent",
        "Reasoning Agent",
        "Writer Agent",
    }

    db = client.app.state.testing_session_factory()
    try:
        workflow = db.query(WorkflowRun).first()
        assert workflow is not None
        assert workflow.status == "completed"
        assert workflow.attempt_count == 1
        assert workflow.started_at is not None
        assert workflow.completed_at is not None
        assert workflow.result_json is not None
    finally:
        db.close()


def test_agent_run_validates_blank_input(client):
    response = client.post("/agent/run", json={"user_input": "   "})

    assert response.status_code == 422


def test_openai_agent_runtime_requires_credentials(client, monkeypatch):
    monkeypatch.setattr("app.api.dependencies.settings.AGENT_RUNTIME", "openai")
    monkeypatch.setattr(
        "app.agents.openai_orchestrator.settings.OPENAI_API_KEY",
        "",
    )

    response = client.post("/agent/run", json={"user_input": "Plan my work"})

    assert response.status_code == 502
    assert response.json() == {
        "detail": "OpenAI agent credentials are not configured"
    }


def test_openai_agent_runtime_persists_mocked_sdk_result(client, monkeypatch):
    async def fake_run(*args, **kwargs):
        return SimpleNamespace(final_output="Grounded OpenAI answer", new_items=[])

    monkeypatch.setattr("app.api.dependencies.settings.AGENT_RUNTIME", "openai")
    monkeypatch.setattr(
        "app.agents.openai_orchestrator.settings.OPENAI_API_KEY",
        "test-key",
    )
    monkeypatch.setattr("app.agents.openai_orchestrator.Runner.run", fake_run)

    response = client.post("/agent/run", json={"user_input": "Plan my work"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["final_answer"] == "Grounded OpenAI answer"
    assert payload["steps"][0]["agent"] == "FARAN Workspace Agent"


def test_failed_workflow_can_be_retried(client, monkeypatch):
    db = client.app.state.testing_session_factory()
    try:
        workflow = WorkflowRun(
            user_input="Recover this workflow",
            status="failed",
            attempt_count=1,
            max_attempts=3,
            plan_json="[]",
            last_error="Temporary failure",
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        workflow_id = workflow.id
    finally:
        db.close()

    response = client.post(f"/agent/workflows/{workflow_id}/retry")

    assert response.status_code == 200
    assert response.json()["workflow_id"] == workflow_id

    db = client.app.state.testing_session_factory()
    try:
        recovered = db.query(WorkflowRun).filter_by(id=workflow_id).one()
        assert recovered.status == "completed"
        assert recovered.attempt_count == 2
        assert recovered.last_error is None
    finally:
        db.close()


def test_completed_workflow_cannot_be_retried(client):
    response = client.post("/agent/run", json={"user_input": "Complete this"})
    workflow_id = response.json()["workflow_id"]

    retry_response = client.post(f"/agent/workflows/{workflow_id}/retry")

    assert retry_response.status_code == 409


def test_missing_workflow_retry_returns_not_found(client):
    response = client.post("/agent/workflows/999/retry")

    assert response.status_code == 404
