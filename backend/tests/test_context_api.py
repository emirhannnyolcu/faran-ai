import app.services.note_service as note_service_module
from app.schemas.ai import NoteAnalysis


def fake_analyze_note(content: str) -> NoteAnalysis:
    return NoteAnalysis(
        summary=f"Memory about {content}",
        topic="Learning",
        tags=["python", "practice"],
        importance=5,
        ai_insights="This should help future context assembly.",
    )


def test_context_assembly_returns_relevant_memory_package(client, monkeypatch):
    monkeypatch.setattr(note_service_module, "analyze_note", fake_analyze_note)
    client.post("/notes/", json={"title": "Python", "content": "Python practice"})
    client.post("/notes/", json={"title": "Habits", "content": "daily practice"})

    response = client.post(
        "/context/assemble",
        json={"query": "python practice", "limit": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "python practice"
    assert len(payload["primary_memories"]) == 2
    assert "Primary memory:" in payload["context_text"]
    assert "Connected memory:" in payload["context_text"]


def test_context_assembly_validates_blank_query(client):
    response = client.post("/context/assemble", json={"query": "   "})

    assert response.status_code == 422
