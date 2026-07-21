from typing import Protocol

from app.memory.schemas import MemoryCandidate


class MemoryIndexer(Protocol):
    """Port for indexing memory candidates for future retrieval."""

    def index(self, candidate: MemoryCandidate) -> None:
        """Index a memory candidate."""


class MemoryRetriever(Protocol):
    """Port for retrieving memory candidates."""

    def search(self, query: str, limit: int = 5) -> list[MemoryCandidate]:
        """Search memory candidates."""
