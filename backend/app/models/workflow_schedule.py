from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.core.database import Base


class WorkflowSchedule(Base):
    """Durable schedule that triggers FARAN agent workflows."""

    __tablename__ = "workflow_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_input = Column(Text, nullable=False)
    runtime = Column(String(50), nullable=False)
    conversation_id = Column(String(128), nullable=True)
    next_run_at = Column(DateTime, nullable=False, index=True)
    interval_seconds = Column(Integer, nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    last_workflow_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
