from app.memory.ports import MemoryIndexer, MemoryRetriever
from app.memory.schemas import MemoryCandidate


class NoOpMemoryIndexer:
    """Indexer placeholder until embeddings/vector storage are introduced."""

    def index(self, candidate: MemoryCandidate) -> None:
        """Accept a candidate without indexing it."""
        return None


class NoOpMemoryRetriever:
    """Retriever placeholder until semantic search is introduced."""

    def search(self, query: str, limit: int = 5) -> list[MemoryCandidate]:
        """Return no results until retrieval is implemented."""
        return []


def get_memory_indexer() -> MemoryIndexer:
    """Return the configured memory indexer."""
    return NoOpMemoryIndexer()


def get_memory_retriever() -> MemoryRetriever:
    """Return the configured memory retriever."""
    return NoOpMemoryRetriever()
