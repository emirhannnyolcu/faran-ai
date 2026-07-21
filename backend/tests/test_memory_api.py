import app.services.note_service as note_service_module
from app.schemas.ai import NoteAnalysis


def fake_analyze_note(content: str) -> NoteAnalysis:
    return NoteAnalysis(
        summary=f"Summary for {content}",
        topic="Second Brain",
        tags=["memory", "ideas"],
        importance=4,
        ai_insights="This idea should connect to related memories.",
    )


def test_memory_timeline_and_connections_api(client, monkeypatch):
    monkeypatch.setattr(note_service_module, "analyze_note", fake_analyze_note)

    first = client.post(
        "/notes/",
        json={"title": "First idea", "content": "Connect ideas over time."},
    )
    second = client.post(
        "/notes/",
        json={"title": "Second idea", "content": "Memory connects related ideas."},
    )

    assert first.status_code == 200
    assert second.status_code == 200

    timeline = client.get("/memory/")
    assert timeline.status_code == 200
    memories = timeline.json()
    assert len(memories) == 2
    assert memories[0]["topic"] == "Second Brain"

    memory_detail = client.get("/memory/2")
    assert memory_detail.status_code == 200
    assert memory_detail.json()["source_title"] == "Second idea"

    connections = client.get("/memory/2/connections")
    assert connections.status_code == 200
    payload = connections.json()
    assert len(payload) == 1
    assert payload[0]["connection"]["target_memory_id"] == 1
    assert "Second Brain" in payload[0]["connection"]["reason"]
    assert payload[0]["target_memory"]["source_title"] == "First idea"


def test_missing_memory_returns_404(client):
    response = client.get("/memory/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Memory not found"}
