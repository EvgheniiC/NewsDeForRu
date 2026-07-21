"""Add source URL health fields on processed_news."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260721_01"
down_revision: str | None = "20260626_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names: set[str] = set(inspector.get_table_names())
    if "processed_news" not in table_names:
        return

    cols: set[str] = {c["name"] for c in inspector.get_columns("processed_news")}
    if "source_url_status" not in cols:
        op.add_column(
            "processed_news",
            sa.Column(
                "source_url_status",
                sa.String(length=16),
                nullable=False,
                server_default="unknown",
            ),
        )
    if "source_url_checked_at" not in cols:
        op.add_column(
            "processed_news",
            sa.Column("source_url_checked_at", sa.DateTime(), nullable=True),
        )
    if "source_url_http_status" not in cols:
        op.add_column(
            "processed_news",
            sa.Column("source_url_http_status", sa.Integer(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names: set[str] = set(inspector.get_table_names())
    if "processed_news" not in table_names:
        return

    cols: set[str] = {c["name"] for c in inspector.get_columns("processed_news")}
    if "source_url_http_status" in cols:
        op.drop_column("processed_news", "source_url_http_status")
    if "source_url_checked_at" in cols:
        op.drop_column("processed_news", "source_url_checked_at")
    if "source_url_status" in cols:
        op.drop_column("processed_news", "source_url_status")
