"""Add image_url to raw_news_items and processed_news."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260429_01"
down_revision: str | None = "20260428_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("raw_news_items"):
        return
    cols_raw: set[str] = {c["name"] for c in inspector.get_columns("raw_news_items")}
    if "image_url" not in cols_raw:
        op.add_column("raw_news_items", sa.Column("image_url", sa.String(length=1024), nullable=True))
    if not inspector.has_table("processed_news"):
        return
    cols_proc: set[str] = {c["name"] for c in inspector.get_columns("processed_news")}
    if "image_url" not in cols_proc:
        op.add_column("processed_news", sa.Column("image_url", sa.String(length=1024), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("processed_news"):
        cols: set[str] = {c["name"] for c in inspector.get_columns("processed_news")}
        if "image_url" in cols:
            op.drop_column("processed_news", "image_url")
    if inspector.has_table("raw_news_items"):
        cols_r: set[str] = {c["name"] for c in inspector.get_columns("raw_news_items")}
        if "image_url" in cols_r:
            op.drop_column("raw_news_items", "image_url")
