from app.models.memory_connection import MemoryConnection
from app.models.memory_vector import MemoryVector
from app.memory.embeddings import EmbeddingPipeline, EmbeddingVector
from app.memory.service import MemoryService
from app.memory.retrieval import NoOpMemoryRetriever
from app.repositories.memory_repository import MemoryRepository
from app.schemas.ai import NoteAnalysis


class RecordingIndexer:
    def __init__(self):
        self.indexed = []

    def index(self, candidate):
        self.indexed.append(candidate)


class ReindexEmbeddingProvider:
    def embed(self, document):
        return EmbeddingVector(
            provider="test",
            model="reindex-v1",
            dimensions=2,
            values=[0.0, 1.0],
        )


def test_memory_service_builds_candidate_from_note_analysis():
    analysis = NoteAnalysis(
        summary="A compact memory summary",
        topic="Second Brain",
        tags=["memory", "retrieval"],
        importance=5,
        ai_insights="This should be easy to retrieve later.",
    )

    candidate = MemoryService().build_candidate(
        title="Memory Engine",
        content="Long-term memory starts with normalized facts.",
        analysis=analysis,
    )

    assert candidate.source_type == "note"
    assert candidate.source_title == "Memory Engine"
    assert candidate.source_content == "Long-term memory starts with normalized facts."
    assert candidate.summary == "A compact memory summary"
    assert candidate.topic == "Second Brain"
    assert candidate.tags == ["memory", "retrieval"]
    assert candidate.tags_text == "memory, retrieval"
    assert candidate.importance == 5
    assert candidate.insights == "This should be easy to retrieve later."


def test_memory_service_persists_candidate(client):
    db = client.app.state.testing_session_factory()
    indexer = RecordingIndexer()
    try:
        service = MemoryService(
            MemoryRepository(db),
            indexer=indexer,
        )
        analysis = NoteAnalysis(
            summary="Persistent memory",
            topic="Memory",
            tags=["long-term"],
            importance=3,
            ai_insights="Keep this available for retrieval.",
        )
        candidate = service.build_candidate(
            title="Persistent item",
            content="Memory should survive the request.",
            analysis=analysis,
        )

        memory_item = service.persist_candidate(candidate)
        db.commit()

        assert memory_item.id == 1
        assert memory_item.source_type == "note"
        assert memory_item.summary == "Persistent memory"
        assert memory_item.tags == "long-term"
        assert db.query(MemoryVector).count() == 1
        assert len(indexer.indexed) == 1
        assert indexer.indexed[0].summary == "Persistent memory"
        assert db.query(MemoryConnection).count() == 0
    finally:
        db.close()


def test_memory_service_creates_connections_for_related_memories(client):
    db = client.app.state.testing_session_factory()
    try:
        service = MemoryService(MemoryRepository(db))
        first_analysis = NoteAnalysis(
            summary="A memory about learning Python deeply.",
            topic="Learning",
            tags=["python", "study"],
            importance=4,
            ai_insights="Python learning matters for long-term craft.",
        )
        second_analysis = NoteAnalysis(
            summary="A related note about Python practice habits.",
            topic="Learning",
            tags=["python", "practice"],
            importance=5,
            ai_insights="Practice habits reinforce learning over time.",
        )

        first_candidate = service.build_candidate(
            title="Python learning",
            content="Study Python every morning.",
            analysis=first_analysis,
        )
        first_item = service.persist_candidate(first_candidate)

        second_candidate = service.build_candidate(
            title="Python practice",
            content="Build small Python projects repeatedly.",
            analysis=second_analysis,
        )
        second_item = service.persist_candidate(second_candidate)
        db.commit()

        connections = db.query(MemoryConnection).all()
        assert len(connections) == 1
        assert connections[0].source_memory_id == second_item.id
        assert connections[0].target_memory_id == first_item.id
        assert 0 <= connections[0].score <= 1
        assert "Learning" in connections[0].reason
        assert "line of thought" in connections[0].reason
    finally:
        db.close()


def test_noop_memory_retriever_returns_no_results():
    assert NoOpMemoryRetriever().search("memory") == []


def test_memory_service_reindexes_existing_vectors(client):
    db = client.app.state.testing_session_factory()
    try:
        repository = MemoryRepository(db)
        service = MemoryService(repository)
        candidate = service.build_candidate(
            title="Reindex",
            content="Provider migration",
            analysis=NoteAnalysis(
                summary="Reindex this memory",
                topic="Migration",
                tags=["embedding"],
                importance=4,
                ai_insights="Vectors should be replaceable.",
            ),
        )
        service.persist_candidate(candidate)
        db.commit()

        reindex_service = MemoryService(
            repository,
            embedding_pipeline=EmbeddingPipeline(ReindexEmbeddingProvider()),
        )
        count = reindex_service.reindex_all()
        db.commit()

        vector = db.query(MemoryVector).one()
        assert count == 1
        assert vector.provider == "test"
        assert vector.model == "reindex-v1"
        assert vector.dimensions == 2
    finally:
        db.close()
