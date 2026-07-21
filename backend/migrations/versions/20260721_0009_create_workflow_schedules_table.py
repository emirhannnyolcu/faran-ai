"""create workflow schedules table

Revision ID: 20260721_0009
Revises: 20260721_0008
Create Date: 2026-07-21
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260721_0009"
down_revision: str | None = "20260721_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "workflow_schedules" in inspector.get_table_names():
        required = {
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
        actual = {
            column["name"] for column in inspector.get_columns("workflow_schedules")
        }
        missing = required - actual
        if missing:
            raise RuntimeError(
                "Existing workflow_schedules table is incomplete: "
                + ", ".join(sorted(missing))
            )
        return
    op.create_table(
        "workflow_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_input", sa.Text(), nullable=False),
        sa.Column("runtime", sa.String(length=50), nullable=False),
        sa.Column("conversation_id", sa.String(length=128), nullable=True),
        sa.Column("next_run_at", sa.DateTime(), nullable=False),
        sa.Column("interval_seconds", sa.Integer(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("last_workflow_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflow_schedules_id"), "workflow_schedules", ["id"])
    op.create_index(
        op.f("ix_workflow_schedules_next_run_at"),
        "workflow_schedules",
        ["next_run_at"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_workflow_schedules_next_run_at"),
        table_name="workflow_schedules",
    )
    op.drop_index(op.f("ix_workflow_schedules_id"), table_name="workflow_schedules")
    op.drop_table("workflow_schedules")
