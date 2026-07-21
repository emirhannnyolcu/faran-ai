from sqlalchemy.orm import Session

from app.models.memory_item import MemoryItem


class MemoryRepository:
    """Database access for memory items."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, memory_item: MemoryItem) -> MemoryItem:
        """Persist a memory item within the caller-managed transaction."""
        self.db.add(memory_item)
        self.db.flush()
        self.db.refresh(memory_item)
        return memory_item

    def list_all(self) -> list[MemoryItem]:
        """Return all memory items."""
        return self.db.query(MemoryItem).all()

    def list_timeline(self) -> list[MemoryItem]:
        """Return memory items ordered by newest first."""
        return self.db.query(MemoryItem).order_by(MemoryItem.created_at.desc()).all()

    def get_by_id(self, memory_id: int) -> MemoryItem | None:
        """Return a memory item by id, if it exists."""
        return self.db.query(MemoryItem).filter(MemoryItem.id == memory_id).first()

    def list_connection_candidates(self, exclude_id: int) -> list[MemoryItem]:
        """Return memory items eligible for connection discovery."""
        return (
            self.db.query(MemoryItem)
            .filter(MemoryItem.id != exclude_id)
            .order_by(MemoryItem.created_at.desc())
            .all()
        )
