"""Add full_article_ru cache column to processed_news."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260604_01"
down_revision: str | None = "20260520_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("processed_news"):
        return
    cols: set[str] = {c["name"] for c in inspector.get_columns("processed_news")}
    if "full_article_ru" not in cols:
        op.add_column("processed_news", sa.Column("full_article_ru", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("processed_news"):
        cols: set[str] = {c["name"] for c in inspector.get_columns("processed_news")}
        if "full_article_ru" in cols:
            op.drop_column("processed_news", "full_article_ru")
