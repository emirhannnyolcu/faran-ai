import math
from types import SimpleNamespace

import pytest

from app.memory.embeddings import (
    EmbeddingDocument,
    EmbeddingPipeline,
    LocalHashEmbeddingProvider,
    OpenAIEmbeddingProvider,
    get_embedding_provider,
)
from app.memory.schemas import MemoryCandidate
from app.services.errors import AIServiceError


def build_candidate() -> MemoryCandidate:
    return MemoryCandidate(
        source_type="note",
        source_id=42,
        source_title="Second Brain",
        source_content="FARAN should remember important knowledge.",
        summary="A memory about FARAN's long-term recall.",
        topic="Memory Engine",
        tags=["memory", "second brain"],
        importance=5,
        insights="This memory should be retrievable by meaning later.",
    )


def test_embedding_pipeline_builds_canonical_document():
    document = EmbeddingPipeline(LocalHashEmbeddingProvider()).build_document(
        build_candidate()
    )

    assert document.source_type == "note"
    assert document.source_id == 42
    assert "Title: Second Brain" in document.text
    assert "Topic: Memory Engine" in document.text
    assert "Tags: memory, second brain" in document.text
    assert document.metadata["importance"] == 5


def test_local_hash_embedding_provider_is_deterministic_and_normalized():
    pipeline = EmbeddingPipeline(LocalHashEmbeddingProvider())
    candidate = build_candidate()

    first = pipeline.embed_candidate(candidate)
    second = pipeline.embed_candidate(candidate)

    assert first.provider == "local"
    assert first.model == "hash-v1"
    assert first.dimensions == 32
    assert first.values == second.values
    assert math.isclose(
        math.sqrt(sum(value * value for value in first.values)),
        1.0,
        rel_tol=1e-9,
    )


def test_openai_embedding_provider_returns_provider_vector(monkeypatch):
    provider = OpenAIEmbeddingProvider()
    embeddings = SimpleNamespace(
        create=lambda **kwargs: SimpleNamespace(
            data=[SimpleNamespace(embedding=[0.25, 0.5, 0.75])]
        )
    )
    monkeypatch.setattr(
        provider,
        "_get_client",
        lambda: SimpleNamespace(embeddings=embeddings),
    )

    vector = provider.embed(EmbeddingDocument(source_type="query", text="memory"))

    assert vector.provider == "openai"
    assert vector.model == "text-embedding-3-small"
    assert vector.dimensions == 3
    assert vector.values == [0.25, 0.5, 0.75]


def test_openai_embedding_provider_requires_credentials(monkeypatch):
    monkeypatch.setattr("app.memory.embeddings.settings.OPENAI_API_KEY", "")

    with pytest.raises(AIServiceError) as exc_info:
        OpenAIEmbeddingProvider().embed(
            EmbeddingDocument(source_type="query", text="memory")
        )

    assert exc_info.value.message == "OpenAI embedding credentials are not configured"


def test_embedding_provider_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr("app.memory.embeddings.settings.EMBEDDING_PROVIDER", "unknown")

    with pytest.raises(AIServiceError):
        get_embedding_provider()
