"""Push subscriptions (FCM) and push_notified_at on processed_news."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260626_01"
down_revision: str | None = "20260623_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names: set[str] = set(inspector.get_table_names())

    if "push_subscriptions" not in table_names:
        op.create_table(
            "push_subscriptions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("device_token", sa.String(length=512), nullable=False),
            sa.Column("platform", sa.String(length=16), nullable=False, server_default="android"),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("device_token", name="uq_push_subscriptions_device_token"),
        )
        op.create_index(
            "ix_push_subscriptions_device_token",
            "push_subscriptions",
            ["device_token"],
            unique=False,
        )

    if "processed_news" in table_names:
        cols: set[str] = {c["name"] for c in inspector.get_columns("processed_news")}
        if "push_notified_at" not in cols:
            op.add_column(
                "processed_news",
                sa.Column("push_notified_at", sa.DateTime(), nullable=True),
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names: set[str] = set(inspector.get_table_names())

    if "processed_news" in table_names:
        cols: set[str] = {c["name"] for c in inspector.get_columns("processed_news")}
        if "push_notified_at" in cols:
            op.drop_column("processed_news", "push_notified_at")

    if "push_subscriptions" in table_names:
        op.drop_index("ix_push_subscriptions_device_token", table_name="push_subscriptions")
        op.drop_table("push_subscriptions")
