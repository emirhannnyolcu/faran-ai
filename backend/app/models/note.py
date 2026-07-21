from datetime import UTC, datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.core.database import Base


class Note(Base):
    """Persisted note and AI-generated analysis metadata."""

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)

    topic = Column(String(255), nullable=True)
    tags = Column(Text, nullable=True)
    importance = Column(Integer, default=1)
    ai_insights = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
