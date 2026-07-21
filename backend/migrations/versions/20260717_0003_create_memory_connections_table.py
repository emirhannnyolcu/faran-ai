"""create memory connections table

Revision ID: 20260717_0003
Revises: 20260717_0002
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260717_0003"
down_revision: str | None = "20260717_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "memory_connections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_memory_id", sa.Integer(), nullable=False),
        sa.Column("target_memory_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_memory_connections_id"),
        "memory_connections",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_memory_connections_source_memory_id"),
        "memory_connections",
        ["source_memory_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_memory_connections_target_memory_id"),
        "memory_connections",
        ["target_memory_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_memory_connections_target_memory_id"),
        table_name="memory_connections",
    )
    op.drop_index(
        op.f("ix_memory_connections_source_memory_id"),
        table_name="memory_connections",
    )
    op.drop_index(op.f("ix_memory_connections_id"), table_name="memory_connections")
    op.drop_table("memory_connections")
