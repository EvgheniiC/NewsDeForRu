"""Alembic migration: reader accounts (optional app login)."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260520_01"
down_revision: str | None = "20260515_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables: set[str] = set(inspector.get_table_names())
    if "reader_users" not in tables:
        op.create_table(
            "reader_users",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.Text(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_reader_users_email", "reader_users", ["email"], unique=True)
    if "reader_refresh_tokens" not in tables:
        op.create_table(
            "reader_refresh_tokens",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("reader_user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["reader_user_id"], ["reader_users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_reader_refresh_tokens_reader_user_id"),
            "reader_refresh_tokens",
            ["reader_user_id"],
        )
        op.create_index(
            op.f("ix_reader_refresh_tokens_token_hash"),
            "reader_refresh_tokens",
            ["token_hash"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "reader_refresh_tokens" in inspector.get_table_names():
        op.drop_table("reader_refresh_tokens")
    if "reader_users" in inspector.get_table_names():
        op.drop_table("reader_users")
