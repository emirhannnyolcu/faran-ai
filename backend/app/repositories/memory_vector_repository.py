import json

from sqlalchemy.orm import Session

from app.memory.embeddings import EmbeddingVector
from app.models.memory_vector import MemoryVector


class MemoryVectorRepository:
    """SQLite-backed vector storage for memory embeddings."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert(self, memory_id: int, vector: EmbeddingVector) -> MemoryVector:
        """Create or replace the vector for a memory item."""
        existing = self.get_by_memory_id(memory_id)
        if existing is None:
            existing = MemoryVector(memory_id=memory_id)
            self.db.add(existing)

        existing.provider = vector.provider
        existing.model = vector.model
        existing.dimensions = vector.dimensions
        existing.values_json = json.dumps(vector.values)
        self.db.flush()
        self.db.refresh(existing)
        return existing

    def get_by_memory_id(self, memory_id: int) -> MemoryVector | None:
        """Return the stored vector for a memory item."""
        return (
            self.db.query(MemoryVector)
            .filter(MemoryVector.memory_id == memory_id)
            .first()
        )

    def list_all(self) -> list[MemoryVector]:
        """Return all stored vectors."""
        return self.db.query(MemoryVector).all()


def vector_from_model(model: MemoryVector) -> EmbeddingVector:
    """Convert a stored vector model into an embedding vector."""
    return EmbeddingVector(
        provider=model.provider,
        model=model.model,
        dimensions=model.dimensions,
        values=json.loads(model.values_json),
    )
