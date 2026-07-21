from logging.config import fileConfig
import logging

from alembic import context
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import engine_from_config, pool
import sqlalchemy as sa

from app.core.settings import settings
from app.core.database import Base
from app.models.memory_connection import MemoryConnection
from app.models.memory_item import MemoryItem
from app.models.memory_vector import MemoryVector
from app.models.note import Note
from app.models.workflow_run import WorkflowRun
from app.models.agent_feedback import AgentFeedback
from app.models.workflow_schedule import WorkflowSchedule


config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
logger = logging.getLogger("alembic.env")


_LEGACY_REVISIONS = [
    (
        "20260717_0001",
        "notes",
        {"id", "title", "content", "summary", "topic", "tags", "importance", "ai_insights", "created_at"},
    ),
    (
        "20260717_0002",
        "memory_items",
        {"id", "source_type", "source_id", "source_title", "source_content", "summary", "topic", "tags", "importance", "insights", "created_at"},
    ),
    (
        "20260717_0003",
        "memory_connections",
        {"id", "source_memory_id", "target_memory_id", "score", "reason", "created_at"},
    ),
    (
        "20260717_0004",
        "memory_vectors",
        {"id", "memory_id", "provider", "model", "dimensions", "values_json", "created_at"},
    ),
    (
        "20260720_0005",
        "workflow_runs",
        {"id", "user_input", "status", "plan_json", "result_json", "created_at", "updated_at"},
    ),
]
_WORKFLOW_RECOVERY_COLUMNS = {
    "attempt_count",
    "max_attempts",
    "last_error",
    "started_at",
    "completed_at",
}
_WORKFLOW_CONVERSATION_COLUMNS = {
    "runtime",
    "conversation_id",
    "response_id",
}
_AGENT_FEEDBACK_COLUMNS = {
    "id",
    "workflow_id",
    "correction",
    "expected_outcome",
    "regression_case_json",
    "suggested_task",
    "status",
    "created_at",
}
_WORKFLOW_SCHEDULE_COLUMNS = {
    "id",
    "user_input",
    "runtime",
    "conversation_id",
    "next_run_at",
    "interval_seconds",
    "enabled",
    "last_workflow_id",
    "created_at",
    "updated_at",
}


def adopt_legacy_schema(connection) -> None:
    """Stamp a verified pre-Alembic FARAN schema without modifying its data."""
    migration_context = MigrationContext.configure(connection)
    if migration_context.get_current_revision() is not None:
        return

    inspector = sa.inspect(connection)
    tables = set(inspector.get_table_names())
    application_tables = {table for _, table, _ in _LEGACY_REVISIONS}
    if not tables.intersection(application_tables):
        return

    matched_revision: str | None = None
    found_gap = False
    for revision, table, required_columns in _LEGACY_REVISIONS:
        if table not in tables:
            found_gap = True
            continue
        if found_gap:
            raise RuntimeError(
                f"Cannot adopt legacy database: table '{table}' exists out of revision order"
            )
        actual_columns = {column["name"] for column in inspector.get_columns(table)}
        missing_columns = required_columns - actual_columns
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise RuntimeError(
                f"Cannot adopt legacy database: table '{table}' is missing {missing}"
            )
        matched_revision = revision

    if matched_revision == "20260720_0005":
        workflow_columns = {
            column["name"] for column in inspector.get_columns("workflow_runs")
        }
        recovery_columns = workflow_columns.intersection(_WORKFLOW_RECOVERY_COLUMNS)
        if recovery_columns and recovery_columns != _WORKFLOW_RECOVERY_COLUMNS:
            raise RuntimeError(
                "Cannot adopt legacy database: workflow recovery columns are incomplete"
            )
        if recovery_columns == _WORKFLOW_RECOVERY_COLUMNS:
            matched_revision = "20260720_0006"

    if matched_revision == "20260720_0006":
        workflow_columns = {
            column["name"] for column in inspector.get_columns("workflow_runs")
        }
        conversation_columns = workflow_columns.intersection(
            _WORKFLOW_CONVERSATION_COLUMNS
        )
        if conversation_columns and conversation_columns != _WORKFLOW_CONVERSATION_COLUMNS:
            raise RuntimeError(
                "Cannot adopt legacy database: workflow conversation columns are incomplete"
            )
        if conversation_columns == _WORKFLOW_CONVERSATION_COLUMNS:
            matched_revision = "20260721_0007"

    if matched_revision == "20260721_0007" and "agent_feedback" in tables:
        feedback_columns = {
            column["name"] for column in inspector.get_columns("agent_feedback")
        }
        missing_feedback_columns = _AGENT_FEEDBACK_COLUMNS - feedback_columns
        if missing_feedback_columns:
            missing = ", ".join(sorted(missing_feedback_columns))
            raise RuntimeError(
                f"Cannot adopt legacy database: agent_feedback is missing {missing}"
            )
        matched_revision = "20260721_0008"

    if matched_revision == "20260721_0008" and "workflow_schedules" in tables:
        schedule_columns = {
            column["name"] for column in inspector.get_columns("workflow_schedules")
        }
        missing_schedule_columns = _WORKFLOW_SCHEDULE_COLUMNS - schedule_columns
        if missing_schedule_columns:
            missing = ", ".join(sorted(missing_schedule_columns))
            raise RuntimeError(
                f"Cannot adopt legacy database: workflow_schedules is missing {missing}"
            )
        matched_revision = "20260721_0009"

    if matched_revision is None:
        return

    logger.warning("Adopting verified legacy FARAN schema at %s", matched_revision)
    migration_context.stamp(ScriptDirectory.from_config(config), matched_revision)


def run_migrations_offline() -> None:
    """Run migrations without a live database connection."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        adopt_legacy_schema(connection)
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
