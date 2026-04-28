"""Add user_engagement_events for anonymous engagement analytics."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260428_01"
down_revision: str | None = "20260427_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("processed_news"):
        return
    if inspector.has_table("user_engagement_events"):
        return
    op.create_table(
        "user_engagement_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("anonymous_user_id", sa.String(length=36), nullable=False),
        sa.Column("processed_news_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("client_event_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(
            ["processed_news_id"],
            ["processed_news.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("client_event_id", name="uq_user_engagement_events_client_event_id"),
    )
    op.create_index(
        "ix_user_engagement_events_anonymous_user_id",
        "user_engagement_events",
        ["anonymous_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_engagement_events_processed_news_id",
        "user_engagement_events",
        ["processed_news_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_engagement_anon_news_type",
        "user_engagement_events",
        ["anonymous_user_id", "processed_news_id", "event_type"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("user_engagement_events"):
        return
    op.drop_index("ix_user_engagement_anon_news_type", table_name="user_engagement_events")
    op.drop_index("ix_user_engagement_events_processed_news_id", table_name="user_engagement_events")
    op.drop_index("ix_user_engagement_events_anonymous_user_id", table_name="user_engagement_events")
    op.drop_table("user_engagement_events")
