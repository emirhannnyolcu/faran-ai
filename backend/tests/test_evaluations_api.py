import app.services.note_service as note_service_module
from app.schemas.ai import NoteAnalysis


def fake_analyze_note(content: str) -> NoteAnalysis:
    return NoteAnalysis(
        summary=f"Eval memory for {content}",
        topic="Evaluation",
        tags=["quality"],
        importance=4,
        ai_insights="This memory should satisfy smoke evals.",
    )


def test_smoke_evaluation_reports_memory_quality(client, monkeypatch):
    monkeypatch.setattr(note_service_module, "analyze_note", fake_analyze_note)
    client.post("/notes/", json={"title": "Eval", "content": "quality memory"})

    response = client.get("/evaluations/smoke")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "faran_memory_smoke_eval"
    assert payload["passed"] is True
    assert {metric["name"] for metric in payload["metrics"]} == {
        "memory_presence",
        "high_importance_signal",
        "topic_coverage",
    }


def test_smoke_evaluation_fails_without_memory(client):
    response = client.get("/evaluations/smoke")

    assert response.status_code == 200
    assert response.json()["passed"] is False


def test_retrieval_evaluation_reports_hit_rate_and_mrr(client, monkeypatch):
    monkeypatch.setattr(note_service_module, "analyze_note", fake_analyze_note)
    created = client.post(
        "/notes/",
        json={"title": "Eval", "content": "quality memory"},
    ).json()

    response = client.post(
        "/evaluations/retrieval",
        json={
            "cases": [
                {
                    "query": "quality memory",
                    "expected_memory_id": created["id"],
                }
            ],
            "limit": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "faran_semantic_retrieval_eval"
    assert payload["passed"] is True
    assert {metric["name"] for metric in payload["metrics"]} == {
        "hit_rate_at_5",
        "mean_reciprocal_rank",
    }


def test_retrieval_evaluation_requires_at_least_one_case(client):
    response = client.post(
        "/evaluations/retrieval",
        json={"cases": [], "limit": 5},
    )

    assert response.status_code == 422


def test_agent_evaluation_and_feedback_create_regression_case(client):
    workflow = client.post(
        "/agent/run",
        json={"user_input": "Build a measurable review routine"},
    ).json()

    evaluation = client.get(f"/evaluations/agent/{workflow['workflow_id']}")
    feedback = client.post(
        "/evaluations/feedback",
        json={
            "workflow_id": workflow["workflow_id"],
            "correction": "The result must include a weekly measurement checkpoint.",
            "expected_outcome": "Include a weekly measurement checkpoint",
        },
    )
    listed = client.get(
        f"/evaluations/agent/{workflow['workflow_id']}/feedback"
    )

    assert evaluation.status_code == 200
    assert evaluation.json()["passed"] is True
    assert feedback.status_code == 201
    assert feedback.json()["regression_case"]["assertion"] == (
        "expected_terms_present"
    )
    assert "measurement" in feedback.json()["regression_case"]["expected_terms"]
    assert len(listed.json()) == 1
