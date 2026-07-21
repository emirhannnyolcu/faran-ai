import hashlib
import math
from typing import Protocol

from openai import APIError, APITimeoutError, OpenAI
from pydantic import BaseModel, Field

from app.core.settings import settings
from app.memory.schemas import MemoryCandidate
from app.services.errors import AIServiceError


class EmbeddingDocument(BaseModel):
    """Canonical text prepared for embedding generation."""

    source_type: str
    source_id: int | None = None
    text: str
    metadata: dict[str, str | int | None] = Field(default_factory=dict)


class EmbeddingVector(BaseModel):
    """Embedding output generated from a canonical document."""

    provider: str
    model: str
    dimensions: int
    values: list[float]


class EmbeddingProvider(Protocol):
    """Provider contract for embedding generation."""

    def embed(self, document: EmbeddingDocument) -> EmbeddingVector:
        """Generate an embedding vector for a document."""


class LocalHashEmbeddingProvider:
    """Deterministic local embedding provider for development and tests."""

    provider = "local"
    model = "hash-v1"
    dimensions = 32

    def embed(self, document: EmbeddingDocument) -> EmbeddingVector:
        """Generate a stable normalized vector from document text."""
        digest = hashlib.sha256(document.text.encode("utf-8")).digest()
        values = [((byte / 255.0) * 2.0) - 1.0 for byte in digest]
        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        normalized = [value / norm for value in values]

        return EmbeddingVector(
            provider=self.provider,
            model=self.model,
            dimensions=self.dimensions,
            values=normalized,
        )


class OpenAIEmbeddingProvider:
    """Generate production embeddings with the OpenAI Embeddings API."""

    provider = "openai"

    def _get_client(self) -> OpenAI:
        if not settings.OPENAI_API_KEY:
            raise AIServiceError("OpenAI embedding credentials are not configured")

        return OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.AI_TIMEOUT_SECONDS,
            max_retries=settings.AI_MAX_RETRIES,
        )

    def embed(self, document: EmbeddingDocument) -> EmbeddingVector:
        """Generate one validated embedding vector for a document."""
        try:
            response = self._get_client().embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=document.text,
                encoding_format="float",
            )
        except APITimeoutError as exc:
            raise AIServiceError("Embedding provider request timed out") from exc
        except APIError as exc:
            raise AIServiceError("Embedding provider request failed") from exc

        if not response.data or not response.data[0].embedding:
            raise AIServiceError("Embedding provider returned an empty vector")

        values = list(response.data[0].embedding)
        return EmbeddingVector(
            provider=self.provider,
            model=settings.OPENAI_EMBEDDING_MODEL,
            dimensions=len(values),
            values=values,
        )


class EmbeddingPipeline:
    """Prepare memory candidates for future vector storage and retrieval."""

    def __init__(self, provider: EmbeddingProvider | None = None) -> None:
        self.provider = provider or get_embedding_provider()

    def build_document(self, candidate: MemoryCandidate) -> EmbeddingDocument:
        """Build canonical text optimized for Second Brain retrieval."""
        text_parts = [
            f"Title: {candidate.source_title}",
            f"Topic: {candidate.topic}",
            f"Summary: {candidate.summary}",
            f"Tags: {candidate.tags_text}",
            f"Insights: {candidate.insights}",
            f"Content: {candidate.source_content}",
        ]

        return EmbeddingDocument(
            source_type=candidate.source_type,
            source_id=candidate.source_id,
            text="\n".join(part for part in text_parts if part.strip()),
            metadata={
                "source_type": candidate.source_type,
                "source_id": candidate.source_id,
                "topic": candidate.topic,
                "importance": candidate.importance,
                "tags": candidate.tags_text,
            },
        )

    def embed_candidate(self, candidate: MemoryCandidate) -> EmbeddingVector:
        """Generate an embedding vector for a memory candidate."""
        return self.provider.embed(self.build_document(candidate))


def cosine_similarity(first: EmbeddingVector, second: EmbeddingVector) -> float:
    """Return cosine similarity for two normalized embedding vectors."""
    if first.dimensions != second.dimensions:
        raise ValueError("Embedding dimensions do not match")

    return sum(
        first_value * second_value
        for first_value, second_value in zip(first.values, second.values, strict=True)
    )


def get_embedding_provider() -> EmbeddingProvider:
    """Return the configured embedding provider."""
    provider = settings.EMBEDDING_PROVIDER.lower()
    if provider == "local":
        return LocalHashEmbeddingProvider()
    if provider == "openai":
        return OpenAIEmbeddingProvider()

    raise AIServiceError("Unsupported embedding provider")
