"""add workflow recovery fields

Revision ID: 20260720_0006
Revises: 20260720_0005
Create Date: 2026-07-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260720_0006"
down_revision: str | None = "20260720_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workflow_runs",
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "workflow_runs",
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
    )
    op.add_column("workflow_runs", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column("workflow_runs", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("workflow_runs", sa.Column("completed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("workflow_runs", "completed_at")
    op.drop_column("workflow_runs", "started_at")
    op.drop_column("workflow_runs", "last_error")
    op.drop_column("workflow_runs", "max_attempts")
    op.drop_column("workflow_runs", "attempt_count")
