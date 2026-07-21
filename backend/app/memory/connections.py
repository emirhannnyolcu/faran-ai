import re
from dataclasses import dataclass

from app.memory.embeddings import EmbeddingPipeline, EmbeddingVector, cosine_similarity
from app.memory.schemas import MemoryCandidate
from app.models.memory_connection import MemoryConnection
from app.models.memory_item import MemoryItem
from app.repositories.memory_connection_repository import MemoryConnectionRepository
from app.repositories.memory_repository import MemoryRepository


@dataclass(frozen=True)
class DiscoveredConnection:
    """Connection candidate discovered between two memories."""

    target_memory: MemoryItem
    score: float
    reason: str


class MemoryConnectionService:
    """Discover and persist idea connections between memory items."""

    def __init__(
        self,
        memory_repository: MemoryRepository,
        connection_repository: MemoryConnectionRepository,
        embedding_pipeline: EmbeddingPipeline | None = None,
    ) -> None:
        self.memory_repository = memory_repository
        self.connection_repository = connection_repository
        self.embedding_pipeline = embedding_pipeline or EmbeddingPipeline()

    def discover_connections(
        self,
        source_memory: MemoryItem,
        source_candidate: MemoryCandidate,
        limit: int = 3,
    ) -> list[DiscoveredConnection]:
        """Find the strongest connections from a new memory to previous memories."""
        source_embedding = self.embedding_pipeline.embed_candidate(source_candidate)
        discoveries: list[DiscoveredConnection] = []

        for target_memory in self.memory_repository.list_connection_candidates(
            exclude_id=source_memory.id,
        ):
            target_candidate = memory_item_to_candidate(target_memory)
            target_embedding = self.embedding_pipeline.embed_candidate(target_candidate)
            score = _connection_score(
                source_candidate=source_candidate,
                target_candidate=target_candidate,
                source_embedding=source_embedding,
                target_embedding=target_embedding,
            )
            discoveries.append(
                DiscoveredConnection(
                    target_memory=target_memory,
                    score=round(score, 6),
                    reason=_connection_reason(source_candidate, target_candidate),
                )
            )

        return sorted(discoveries, key=lambda item: item.score, reverse=True)[:limit]

    def persist_connections(
        self,
        source_memory: MemoryItem,
        discoveries: list[DiscoveredConnection],
    ) -> list[MemoryConnection]:
        """Persist discovered memory connections."""
        connections = [
            MemoryConnection(
                source_memory_id=source_memory.id,
                target_memory_id=discovery.target_memory.id,
                score=discovery.score,
                reason=discovery.reason,
            )
            for discovery in discoveries
        ]

        return self.connection_repository.create_many(connections)


def memory_item_to_candidate(memory_item: MemoryItem) -> MemoryCandidate:
    """Convert a persisted memory item back into a candidate shape."""
    tags = [
        tag.strip()
        for tag in (memory_item.tags or "").split(",")
        if tag.strip()
    ]

    return MemoryCandidate(
        source_type=memory_item.source_type,
        source_id=memory_item.source_id,
        source_title=memory_item.source_title,
        source_content=memory_item.source_content,
        summary=memory_item.summary,
        topic=memory_item.topic,
        tags=tags,
        importance=memory_item.importance,
        insights=memory_item.insights,
    )


def _connection_score(
    source_candidate: MemoryCandidate,
    target_candidate: MemoryCandidate,
    source_embedding: EmbeddingVector,
    target_embedding: EmbeddingVector,
) -> float:
    cosine = (cosine_similarity(source_embedding, target_embedding) + 1.0) / 2.0
    lexical = _lexical_overlap(source_candidate, target_candidate)
    return (cosine * 0.65) + (lexical * 0.35)


def _lexical_overlap(
    source_candidate: MemoryCandidate,
    target_candidate: MemoryCandidate,
) -> float:
    source_tokens = _tokens(source_candidate)
    target_tokens = _tokens(target_candidate)
    if not source_tokens or not target_tokens:
        return 0.0

    return len(source_tokens & target_tokens) / len(source_tokens | target_tokens)


def _tokens(candidate: MemoryCandidate) -> set[str]:
    text = " ".join(
        [
            candidate.source_title,
            candidate.source_content,
            candidate.summary,
            candidate.topic,
            candidate.tags_text,
            candidate.insights,
        ]
    )
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2
    }


def _connection_reason(
    source_candidate: MemoryCandidate,
    target_candidate: MemoryCandidate,
) -> str:
    if source_candidate.topic.lower() == target_candidate.topic.lower():
        return (
            f"Both memories focus on {source_candidate.topic}, "
            "so this new idea may extend an existing line of thought."
        )

    shared_tags = sorted(set(source_candidate.tags) & set(target_candidate.tags))
    if shared_tags:
        return (
            f"They share recurring signals around {', '.join(shared_tags)}, "
            "which suggests a meaningful connection."
        )

    return (
        "The language and context are similar enough that FARAN should keep "
        "these memories near each other."
    )
