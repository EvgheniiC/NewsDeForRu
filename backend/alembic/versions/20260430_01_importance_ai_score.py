"""Add importance_ai_score to processed_news (AI 1–10 for Germany residents)."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260430_01"
down_revision: str | None = "20260429_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("processed_news"):
        return
    cols: set[str] = {c["name"] for c in inspector.get_columns("processed_news")}
    if "importance_ai_score" not in cols:
        op.add_column(
            "processed_news",
            sa.Column("importance_ai_score", sa.Integer(), nullable=False, server_default="5"),
        )
        # SQLite does not support ALTER COLUMN ... DROP DEFAULT (see OperationalError).
        if bind.dialect.name != "sqlite":
            op.alter_column("processed_news", "importance_ai_score", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("processed_news"):
        return
    cols: set[str] = {c["name"] for c in inspector.get_columns("processed_news")}
    if "importance_ai_score" in cols:
        op.drop_column("processed_news", "importance_ai_score")
