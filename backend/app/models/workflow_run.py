from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class WorkflowRun(Base):
    """Persisted long-running agent workflow state."""

    __tablename__ = "workflow_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_input = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    plan_json = Column(Text, nullable=True)
    result_json = Column(Text, nullable=True)
    last_error = Column(Text, nullable=True)
    runtime = Column(String(50), nullable=False, default="deterministic")
    conversation_id = Column(String(128), nullable=True, index=True)
    response_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
