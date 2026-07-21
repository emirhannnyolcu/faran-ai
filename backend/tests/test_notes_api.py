import app.services.note_service as note_service_module
from app.models.memory_connection import MemoryConnection
from app.models.memory_item import MemoryItem
from app.schemas.ai import NoteAnalysis


def fake_analyze_note(content: str) -> NoteAnalysis:
    return NoteAnalysis(
        summary="Short summary",
        topic="Knowledge Management",
        tags=["second brain", "ai"],
        importance=4,
        ai_insights="Useful for long-term memory.",
    )


def test_health_returns_application_status(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "version": "0.1.0"}
    assert response.headers["x-request-id"]
    assert response.headers["x-process-time"]


def test_create_list_get_and_delete_note(client, monkeypatch):
    monkeypatch.setattr(note_service_module, "analyze_note", fake_analyze_note)

    create_response = client.post(
        "/notes/",
        json={
            "title": "FARAN Memory Test",
            "content": "FARAN helps organize knowledge over time.",
        },
    )

    assert create_response.status_code == 200
    created_note = create_response.json()
    assert created_note["id"] == 1
    assert created_note["summary"] == "Short summary"
    assert created_note["tags"] == "second brain, ai"
    assert created_note["importance"] == 4

    db = client.app.state.testing_session_factory()
    try:
        memory_items = db.query(MemoryItem).all()
        assert len(memory_items) == 1
        assert memory_items[0].source_type == "note"
        assert memory_items[0].source_id == created_note["id"]
        assert memory_items[0].summary == "Short summary"
        assert memory_items[0].tags == "second brain, ai"
        assert db.query(MemoryConnection).count() == 0
    finally:
        db.close()

    list_response = client.get("/notes/")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get("/notes/1")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "FARAN Memory Test"

    delete_response = client.delete("/notes/1")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "Note deleted successfully"}

    assert client.get("/notes/1").status_code == 404


def test_creating_second_related_note_stores_idea_connection(client, monkeypatch):
    monkeypatch.setattr(note_service_module, "analyze_note", fake_analyze_note)

    first_response = client.post(
        "/notes/",
        json={
            "title": "First FARAN note",
            "content": "FARAN should connect knowledge over time.",
        },
    )
    second_response = client.post(
        "/notes/",
        json={
            "title": "Second FARAN note",
            "content": "FARAN should remember related ideas.",
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    db = client.app.state.testing_session_factory()
    try:
        connections = db.query(MemoryConnection).all()
        assert len(connections) == 1
        assert connections[0].score >= 0
        assert "Knowledge Management" in connections[0].reason
    finally:
        db.close()


def test_create_note_validates_blank_input(client):
    response = client.post(
        "/notes/",
        json={"title": "   ", "content": "Valid content"},
    )

    assert response.status_code == 422


def test_create_note_returns_502_when_ai_is_not_configured(client):
    response = client.post(
        "/notes/",
        json={"title": "Valid title", "content": "Valid content"},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "AI provider credentials are not configured"}
    assert client.get("/notes/").json() == []
