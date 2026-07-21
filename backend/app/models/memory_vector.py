from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class MemoryVector(Base):
    """Stored embedding vector for a memory item."""

    __tablename__ = "memory_vectors"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    dimensions = Column(Integer, nullable=False)
    values_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
