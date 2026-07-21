"""create memory vectors table

Revision ID: 20260717_0004
Revises: 20260717_0003
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260717_0004"
down_revision: str | None = "20260717_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "memory_vectors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("memory_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("values_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_memory_vectors_id"), "memory_vectors", ["id"], unique=False)
    op.create_index(
        op.f("ix_memory_vectors_memory_id"),
        "memory_vectors",
        ["memory_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_memory_vectors_memory_id"), table_name="memory_vectors")
    op.drop_index(op.f("ix_memory_vectors_id"), table_name="memory_vectors")
    op.drop_table("memory_vectors")
