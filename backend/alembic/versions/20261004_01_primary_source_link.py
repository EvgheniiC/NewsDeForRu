"""Store a primary-source link extracted from publisher RSS HTML."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20261004_01"
down_revision: str | None = "20260919_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "raw_news_items" not in set(inspector.get_table_names()):
        return
    cols: set[str] = {column["name"] for column in inspector.get_columns("raw_news_items")}
    if "primary_source_url" not in cols:
        op.add_column(
            "raw_news_items",
            sa.Column("primary_source_url", sa.String(length=1024), nullable=True),
        )
    if "primary_source_name" not in cols:
        op.add_column(
            "raw_news_items",
            sa.Column("primary_source_name", sa.String(length=256), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "raw_news_items" not in set(inspector.get_table_names()):
        return
    cols: set[str] = {column["name"] for column in inspector.get_columns("raw_news_items")}
    if "primary_source_name" in cols:
        op.drop_column("raw_news_items", "primary_source_name")
    if "primary_source_url" in cols:
        op.drop_column("raw_news_items", "primary_source_url")
