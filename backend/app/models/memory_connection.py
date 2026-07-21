from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, Integer, Text

from app.core.database import Base


class MemoryConnection(Base):
    """Persisted relationship between two memory items."""

    __tablename__ = "memory_connections"

    id = Column(Integer, primary_key=True, index=True)
    source_memory_id = Column(Integer, nullable=False, index=True)
    target_memory_id = Column(Integer, nullable=False, index=True)
    score = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
