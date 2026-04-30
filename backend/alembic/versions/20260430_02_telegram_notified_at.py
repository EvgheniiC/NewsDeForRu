"""Track when a processed news item was already sent to Telegram (avoid duplicates)."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260430_02"
down_revision: str | None = "20260430_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("processed_news"):
        return
    cols: set[str] = {c["name"] for c in inspector.get_columns("processed_news")}
    if "telegram_notified_at" not in cols:
        op.add_column(
            "processed_news",
            sa.Column("telegram_notified_at", sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("processed_news"):
        return
    cols: set[str] = {c["name"] for c in inspector.get_columns("processed_news")}
    if "telegram_notified_at" in cols:
        op.drop_column("processed_news", "telegram_notified_at")
