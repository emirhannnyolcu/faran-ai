from sqlalchemy.orm import Session

from app.models.memory_connection import MemoryConnection


class MemoryConnectionRepository:
    """Database access for memory connections."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_many(
        self,
        connections: list[MemoryConnection],
    ) -> list[MemoryConnection]:
        """Persist memory connections within the caller-managed transaction."""
        self.db.add_all(connections)
        self.db.flush()
        for connection in connections:
            self.db.refresh(connection)
        return connections

    def list_by_source(self, source_memory_id: int) -> list[MemoryConnection]:
        """Return connections created for a source memory."""
        return (
            self.db.query(MemoryConnection)
            .filter(MemoryConnection.source_memory_id == source_memory_id)
            .order_by(MemoryConnection.score.desc())
            .all()
        )
