"""add workflow conversation fields

Revision ID: 20260721_0007
Revises: 20260720_0006
Create Date: 2026-07-21
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260721_0007"
down_revision: str | None = "20260720_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workflow_runs",
        sa.Column(
            "runtime",
            sa.String(length=50),
            server_default="deterministic",
            nullable=False,
        ),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("conversation_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("response_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        op.f("ix_workflow_runs_conversation_id"),
        "workflow_runs",
        ["conversation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_workflow_runs_conversation_id"),
        table_name="workflow_runs",
    )
    op.drop_column("workflow_runs", "response_id")
    op.drop_column("workflow_runs", "conversation_id")
    op.drop_column("workflow_runs", "runtime")
