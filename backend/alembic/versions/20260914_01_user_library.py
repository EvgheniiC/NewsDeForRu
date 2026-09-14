"""Per-account saved (useful) and read news for cross-device sync."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260914_01"
down_revision: str | None = "20260802_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names: set[str] = set(inspector.get_table_names())
    if "app_users" not in table_names or "processed_news" not in table_names:
        return
    if "user_saved_news" not in table_names:
        op.create_table(
            "user_saved_news",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("processed_news_id", sa.Integer(), nullable=False),
            sa.Column("marked_at", sa.BigInteger(), nullable=False),
            sa.Column("removed_at", sa.BigInteger(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["processed_news_id"], ["processed_news.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "processed_news_id", name="uq_user_saved_news_user_news"),
        )
        op.create_index("ix_user_saved_news_user_id", "user_saved_news", ["user_id"], unique=False)
        op.create_index(
            "ix_user_saved_news_processed_news_id",
            "user_saved_news",
            ["processed_news_id"],
            unique=False,
        )
    if "user_read_news" not in table_names:
        op.create_table(
            "user_read_news",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("processed_news_id", sa.Integer(), nullable=False),
            sa.Column("read_at", sa.BigInteger(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["processed_news_id"], ["processed_news.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "processed_news_id", name="uq_user_read_news_user_news"),
        )
        op.create_index("ix_user_read_news_user_id", "user_read_news", ["user_id"], unique=False)
        op.create_index(
            "ix_user_read_news_processed_news_id",
            "user_read_news",
            ["processed_news_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names: set[str] = set(inspector.get_table_names())
    if "user_read_news" in table_names:
        op.drop_index("ix_user_read_news_processed_news_id", table_name="user_read_news")
        op.drop_index("ix_user_read_news_user_id", table_name="user_read_news")
        op.drop_table("user_read_news")
    if "user_saved_news" in table_names:
        op.drop_index("ix_user_saved_news_processed_news_id", table_name="user_saved_news")
        op.drop_index("ix_user_saved_news_user_id", table_name="user_saved_news")
        op.drop_table("user_saved_news")
