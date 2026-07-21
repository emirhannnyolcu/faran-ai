"""create agent feedback table

Revision ID: 20260721_0008
Revises: 20260721_0007
Create Date: 2026-07-21
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260721_0008"
down_revision: str | None = "20260721_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "agent_feedback" in inspector.get_table_names():
        required = {
            "id",
            "workflow_id",
            "correction",
            "expected_outcome",
            "regression_case_json",
            "suggested_task",
            "status",
            "created_at",
        }
        actual = {
            column["name"] for column in inspector.get_columns("agent_feedback")
        }
        missing = required - actual
        if missing:
            raise RuntimeError(
                "Existing agent_feedback table is incomplete: "
                + ", ".join(sorted(missing))
            )
        return
    op.create_table(
        "agent_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workflow_id", sa.Integer(), nullable=False),
        sa.Column("correction", sa.Text(), nullable=False),
        sa.Column("expected_outcome", sa.Text(), nullable=False),
        sa.Column("regression_case_json", sa.Text(), nullable=False),
        sa.Column("suggested_task", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_feedback_id"), "agent_feedback", ["id"])
    op.create_index(
        op.f("ix_agent_feedback_workflow_id"),
        "agent_feedback",
        ["workflow_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_agent_feedback_workflow_id"),
        table_name="agent_feedback",
    )
    op.drop_index(op.f("ix_agent_feedback_id"), table_name="agent_feedback")
    op.drop_table("agent_feedback")
