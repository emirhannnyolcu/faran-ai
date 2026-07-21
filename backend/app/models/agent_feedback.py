from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class AgentFeedback(Base):
    """Expert correction converted into a durable regression case."""

    __tablename__ = "agent_feedback"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, nullable=False, index=True)
    correction = Column(Text, nullable=False)
    expected_outcome = Column(Text, nullable=False)
    regression_case_json = Column(Text, nullable=False)
    suggested_task = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="open")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
