"""Add cover_tag illustration key to processed_news."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260919_01"
down_revision: str | None = "20260914_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "processed_news" not in set(inspector.get_table_names()):
        return
    cols: set[str] = {column["name"] for column in inspector.get_columns("processed_news")}
    if "cover_tag" in cols:
        return
    op.add_column(
        "processed_news",
        sa.Column("cover_tag", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "processed_news" not in set(inspector.get_table_names()):
        return
    cols: set[str] = {column["name"] for column in inspector.get_columns("processed_news")}
    if "cover_tag" not in cols:
        return
    op.drop_column("processed_news", "cover_tag")
