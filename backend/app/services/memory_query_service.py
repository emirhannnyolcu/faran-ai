from app.models.memory_connection import MemoryConnection
from app.models.memory_item import MemoryItem
from app.repositories.memory_connection_repository import MemoryConnectionRepository
from app.repositories.memory_repository import MemoryRepository


class MemoryItemNotFoundError(Exception):
    """Raised when a memory item cannot be found."""


class MemoryQueryService:
    """Read-side service for memory timeline and idea connections."""

    def __init__(
        self,
        memory_repository: MemoryRepository,
        connection_repository: MemoryConnectionRepository,
    ) -> None:
        self.memory_repository = memory_repository
        self.connection_repository = connection_repository

    def list_memories(self) -> list[MemoryItem]:
        """Return memory items in timeline order."""
        return self.memory_repository.list_timeline()

    def get_memory(self, memory_id: int) -> MemoryItem:
        """Return a memory item or raise a domain error."""
        memory = self.memory_repository.get_by_id(memory_id)
        if memory is None:
            raise MemoryItemNotFoundError()
        return memory

    def list_connections(self, memory_id: int) -> list[tuple[MemoryConnection, MemoryItem]]:
        """Return connections and target memories for a memory item."""
        self.get_memory(memory_id)
        results: list[tuple[MemoryConnection, MemoryItem]] = []
        for connection in self.connection_repository.list_by_source(memory_id):
            target = self.memory_repository.get_by_id(connection.target_memory_id)
            if target is not None:
                results.append((connection, target))
        return results
