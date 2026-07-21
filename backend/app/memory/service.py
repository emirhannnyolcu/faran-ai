from app.memory.ports import MemoryIndexer
from app.memory.connections import MemoryConnectionService
from app.memory.embeddings import EmbeddingPipeline, EmbeddingVector
from app.memory.retrieval import get_memory_indexer
from app.memory.schemas import MemoryCandidate
from app.models.memory_item import MemoryItem
from app.repositories.memory_connection_repository import MemoryConnectionRepository
from app.repositories.memory_repository import MemoryRepository
from app.repositories.memory_vector_repository import MemoryVectorRepository
from app.schemas.ai import NoteAnalysis


class MemoryService:
    """Prepare note analysis for the long-term memory pipeline."""

    def __init__(
        self,
        repository: MemoryRepository | None = None,
        indexer: MemoryIndexer | None = None,
        embedding_pipeline: EmbeddingPipeline | None = None,
        connection_service: MemoryConnectionService | None = None,
    ) -> None:
        self.repository = repository
        self.indexer = indexer or get_memory_indexer()
        self.embedding_pipeline = embedding_pipeline or EmbeddingPipeline()
        self.connection_service = connection_service

        if self.connection_service is None and self.repository is not None:
            self.connection_service = MemoryConnectionService(
                memory_repository=self.repository,
                connection_repository=MemoryConnectionRepository(self.repository.db),
                embedding_pipeline=self.embedding_pipeline,
            )
        self.vector_repository = (
            MemoryVectorRepository(self.repository.db)
            if self.repository is not None
            else None
        )

    def build_candidate(
        self,
        title: str,
        content: str,
        analysis: NoteAnalysis,
    ) -> MemoryCandidate:
        """Create a normalized memory candidate from a note analysis."""
        return MemoryCandidate(
            source_title=title,
            source_content=content,
            summary=analysis.summary,
            topic=analysis.topic,
            tags=analysis.tags,
            importance=analysis.importance,
            insights=analysis.ai_insights,
        )

    def persist_candidate(self, candidate: MemoryCandidate) -> MemoryItem:
        """Persist a normalized memory candidate."""
        if self.repository is None:
            raise RuntimeError("Memory repository is not configured")

        memory_item = MemoryItem(
            source_type=candidate.source_type,
            source_id=candidate.source_id,
            source_title=candidate.source_title,
            source_content=candidate.source_content,
            summary=candidate.summary,
            topic=candidate.topic,
            tags=candidate.tags_text,
            importance=candidate.importance,
            insights=candidate.insights,
        )

        persisted_item = self.repository.create(memory_item)
        embedding = self.embedding_pipeline.embed_candidate(candidate)
        if self.vector_repository is not None:
            self.vector_repository.upsert(persisted_item.id, embedding)

        if self.connection_service is not None:
            discoveries = self.connection_service.discover_connections(
                source_memory=persisted_item,
                source_candidate=candidate,
            )
            self.connection_service.persist_connections(persisted_item, discoveries)

        self.indexer.index(candidate)
        return persisted_item

    def build_embedding(self, candidate: MemoryCandidate) -> EmbeddingVector:
        """Generate an embedding vector for a memory candidate."""
        return self.embedding_pipeline.embed_candidate(candidate)

    def reindex_all(self) -> int:
        """Replace every stored vector with the configured embedding provider."""
        if self.repository is None or self.vector_repository is None:
            raise RuntimeError("Memory repository is not configured")

        memories = self.repository.list_all()
        for memory in memories:
            candidate = memory_candidate_from_item(memory)
            vector = self.embedding_pipeline.embed_candidate(candidate)
            self.vector_repository.upsert(memory.id, vector)
        return len(memories)


def memory_candidate_from_item(memory: MemoryItem) -> MemoryCandidate:
    """Rebuild the canonical embedding candidate for a persisted memory."""
    return MemoryCandidate(
        source_type=memory.source_type,
        source_id=memory.source_id,
        source_title=memory.source_title,
        source_content=memory.source_content,
        summary=memory.summary,
        topic=memory.topic,
        tags=[tag.strip() for tag in (memory.tags or "").split(",") if tag.strip()],
        importance=memory.importance,
        insights=memory.insights,
    )
