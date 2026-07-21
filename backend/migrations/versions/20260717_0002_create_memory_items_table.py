"""create memory items table

Revision ID: 20260717_0002
Revises: 20260717_0001
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260717_0002"
down_revision: str | None = "20260717_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "memory_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("source_title", sa.String(length=255), nullable=False),
        sa.Column("source_content", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("importance", sa.Integer(), nullable=False),
        sa.Column("insights", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_memory_items_id"), "memory_items", ["id"], unique=False)
    op.create_index(
        op.f("ix_memory_items_source_id"),
        "memory_items",
        ["source_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_memory_items_source_id"), table_name="memory_items")
    op.drop_index(op.f("ix_memory_items_id"), table_name="memory_items")
    op.drop_table("memory_items")
