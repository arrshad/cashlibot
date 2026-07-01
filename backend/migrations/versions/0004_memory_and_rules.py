"""usermemory (pgvector) + categorizationrule

Revision ID: 0004_memory_rules
Revises: 0003_transactions
Create Date: 2026-07-01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0004_memory_rules"
down_revision: str | None = "0003_transactions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIM = 1536


def upgrade() -> None:
    op.create_table(
        "usermemory",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("memory_type", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_usermemory_user_id", "usermemory", ["user_id"])

    op.create_table(
        "categorizationrule",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("merchant_or_keyword", sa.String(), nullable=False),
        sa.Column(
            "category_id",
            sa.UUID(),
            sa.ForeignKey("category.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("match_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_categorizationrule_user_id", "categorizationrule", ["user_id"]
    )
    op.create_index(
        "ix_categorizationrule_keyword",
        "categorizationrule",
        ["merchant_or_keyword"],
    )
    op.create_unique_constraint(
        "uq_categorizationrule_user_keyword",
        "categorizationrule",
        ["user_id", "merchant_or_keyword"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_categorizationrule_user_keyword",
        "categorizationrule",
        type_="unique",
    )
    op.drop_index(
        "ix_categorizationrule_keyword", table_name="categorizationrule"
    )
    op.drop_index(
        "ix_categorizationrule_user_id", table_name="categorizationrule"
    )
    op.drop_table("categorizationrule")
    op.drop_index("ix_usermemory_user_id", table_name="usermemory")
    op.drop_table("usermemory")
