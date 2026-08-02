"""Remove the cached full-article translation column."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260802_01"
down_revision: str | None = "20260721_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Delete cached translations by dropping their dedicated column."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("processed_news"):
        return

    columns: set[str] = {
        str(column["name"]) for column in inspector.get_columns("processed_news")
    }
    if "full_article_ru" in columns:
        op.drop_column("processed_news", "full_article_ru")


def downgrade() -> None:
    """Restore the empty cache column without restoring deleted content."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("processed_news"):
        return

    columns: set[str] = {
        str(column["name"]) for column in inspector.get_columns("processed_news")
    }
    if "full_article_ru" not in columns:
        op.add_column(
            "processed_news",
            sa.Column("full_article_ru", sa.Text(), nullable=True),
        )
