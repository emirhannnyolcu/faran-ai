from app.memory.embeddings import (
    EmbeddingDocument,
    EmbeddingPipeline,
    cosine_similarity,
)
from app.repositories.memory_repository import MemoryRepository
from app.repositories.memory_vector_repository import (
    MemoryVectorRepository,
    vector_from_model,
)
from app.schemas.retrieval import SemanticSearchResponse, SemanticSearchResult


class SemanticRetrievalService:
    """Retrieve memories by semantic similarity."""

    def __init__(
        self,
        memory_repository: MemoryRepository,
        vector_repository: MemoryVectorRepository,
        embedding_pipeline: EmbeddingPipeline | None = None,
    ) -> None:
        self.memory_repository = memory_repository
        self.vector_repository = vector_repository
        self.embedding_pipeline = embedding_pipeline or EmbeddingPipeline()

    def search(self, query: str, limit: int = 5) -> SemanticSearchResponse:
        """Return nearest memories for a query."""
        query_vector = self.embedding_pipeline.provider.embed(
            EmbeddingDocument(source_type="query", text=query)
        )
        results: list[SemanticSearchResult] = []

        for stored_vector in self.vector_repository.list_all():
            memory = self.memory_repository.get_by_id(stored_vector.memory_id)
            if memory is None:
                continue

            stored_embedding = vector_from_model(stored_vector)
            if (
                stored_embedding.provider != query_vector.provider
                or stored_embedding.model != query_vector.model
                or stored_embedding.dimensions != query_vector.dimensions
            ):
                continue
            score = cosine_similarity(query_vector, stored_embedding)
            results.append(
                SemanticSearchResult(memory=memory, score=round(score, 6))
            )

        results.sort(key=lambda result: result.score, reverse=True)
        return SemanticSearchResponse(query=query, results=results[:limit])
