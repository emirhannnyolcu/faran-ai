from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class MemoryItem(Base):
    """Persisted long-term memory item derived from a source object."""

    __tablename__ = "memory_items"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(50), nullable=False)
    source_id = Column(Integer, nullable=True, index=True)
    source_title = Column(String(255), nullable=False)
    source_content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    topic = Column(String(255), nullable=False)
    tags = Column(Text, nullable=True)
    importance = Column(Integer, nullable=False, default=1)
    insights = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
