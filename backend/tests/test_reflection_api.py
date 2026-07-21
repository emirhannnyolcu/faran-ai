import app.services.note_service as note_service_module
from app.schemas.ai import NoteAnalysis


def fake_analyze_note(content: str) -> NoteAnalysis:
    return NoteAnalysis(
        summary=f"Reflection memory for {content}",
        topic="Creative Work",
        tags=["focus", "craft"],
        importance=5,
        ai_insights="This memory reflects a recurring creative pattern.",
    )


def test_reflection_returns_memory_patterns(client, monkeypatch):
    monkeypatch.setattr(note_service_module, "analyze_note", fake_analyze_note)
    client.post("/notes/", json={"title": "Focus", "content": "Deep work"})
    client.post("/notes/", json={"title": "Craft", "content": "Improve craft"})

    response = client.get("/reflection/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_memories"] == 2
    assert payload["recurring_topics"] == ["Creative Work"]
    assert "focus" in payload["recurring_tags"]
    assert payload["high_importance_themes"] == ["Creative Work"]
    assert "Creative Work" in payload["insight"]


def test_reflection_handles_empty_memory(client):
    response = client.get("/reflection/")

    assert response.status_code == 200
    assert response.json()["total_memories"] == 0
