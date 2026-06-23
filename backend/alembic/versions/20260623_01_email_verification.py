"""Email verification for reader registration."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260623_01"
down_revision: str | None = "20260607_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names: set[str] = set(inspector.get_table_names())

    if "app_users" in table_names:
        columns: list[str] = {col["name"] for col in inspector.get_columns("app_users")}
        if "email_verified_at" not in columns:
            op.add_column("app_users", sa.Column("email_verified_at", sa.DateTime(), nullable=True))
            op.execute(
                sa.text(
                    "UPDATE app_users SET email_verified_at = created_at WHERE email_verified_at IS NULL"
                )
            )

    if "email_verification_tokens" not in table_names:
        op.create_table(
            "email_verification_tokens",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("used_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_email_verification_tokens_user_id"),
            "email_verification_tokens",
            ["user_id"],
        )
        op.create_index(
            op.f("ix_email_verification_tokens_token_hash"),
            "email_verification_tokens",
            ["token_hash"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names: set[str] = set(inspector.get_table_names())

    if "email_verification_tokens" in table_names:
        op.drop_table("email_verification_tokens")

    if "app_users" in table_names:
        columns: list[str] = {col["name"] for col in inspector.get_columns("app_users")}
        if "email_verified_at" in columns:
            op.drop_column("app_users", "email_verified_at")
