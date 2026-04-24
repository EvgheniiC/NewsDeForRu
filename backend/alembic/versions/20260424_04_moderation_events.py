"""Add moderation_events audit table.

Revision ID: 20260424_04
Revises: 20260424_03
Create Date: 2026-04-24
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260424_04"
down_revision: str | None = "20260424_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("processed_news"):
        return
    if inspector.has_table("moderation_events"):
        return
    op.create_table(
        "moderation_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("processed_news_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(
            ["processed_news_id"],
            ["processed_news.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_moderation_events_processed_news_id",
        "moderation_events",
        ["processed_news_id"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("moderation_events"):
        return
    op.drop_index("ix_moderation_events_processed_news_id", table_name="moderation_events")
    op.drop_table("moderation_events")
