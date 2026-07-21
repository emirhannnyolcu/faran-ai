import app.services.note_service as note_service_module
from app.memory.embeddings import EmbeddingPipeline, EmbeddingVector
from app.repositories.memory_repository import MemoryRepository
from app.repositories.memory_vector_repository import MemoryVectorRepository
from app.schemas.ai import NoteAnalysis
from app.services.retrieval_service import SemanticRetrievalService


def fake_analyze_note(content: str) -> NoteAnalysis:
    return NoteAnalysis(
        summary=f"Memory about {content}",
        topic="Semantic Retrieval",
        tags=["memory", "search"],
        importance=4,
        ai_insights="This should be retrievable later.",
    )


def test_semantic_retrieval_returns_stored_memories(client, monkeypatch):
    monkeypatch.setattr(note_service_module, "analyze_note", fake_analyze_note)
    client.post("/notes/", json={"title": "Memory Search", "content": "find ideas"})
    client.post("/notes/", json={"title": "Recall", "content": "retrieve memory"})

    response = client.post(
        "/retrieval/semantic-search",
        json={"query": "memory search", "limit": 2},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "memory search"
    assert len(payload["results"]) == 2
    assert "memory" in payload["results"][0]["memory"]["tags"]
    assert isinstance(payload["results"][0]["score"], float)


def test_semantic_retrieval_validates_blank_query(client):
    response = client.post("/retrieval/semantic-search", json={"query": "   "})

    assert response.status_code == 422


class ThreeDimensionEmbeddingProvider:
    def embed(self, document):
        return EmbeddingVector(
            provider="test",
            model="three-dimensions",
            dimensions=3,
            values=[1.0, 0.0, 0.0],
        )


def test_retrieval_skips_vectors_from_a_different_provider(client, monkeypatch):
    monkeypatch.setattr(note_service_module, "analyze_note", fake_analyze_note)
    client.post("/notes/", json={"title": "Local", "content": "local vector"})
    db = client.app.state.testing_session_factory()
    try:
        service = SemanticRetrievalService(
            memory_repository=MemoryRepository(db),
            vector_repository=MemoryVectorRepository(db),
            embedding_pipeline=EmbeddingPipeline(ThreeDimensionEmbeddingProvider()),
        )

        response = service.search("query")

        assert response.results == []
    finally:
        db.close()
