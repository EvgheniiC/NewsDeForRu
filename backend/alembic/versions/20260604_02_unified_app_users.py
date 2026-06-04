"""Merge staff_users and reader_users into app_users; moderation FK → user_id."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260604_02"
down_revision: str | None = "20260604_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _migrate_legacy_accounts(bind: sa.engine.Connection, inspector: inspect.Inspector) -> None:
    tables: set[str] = set(inspector.get_table_names())
    if "staff_users" not in tables:
        return

    bind.execute(
        sa.text(
            """
            INSERT INTO app_users (id, email, password_hash, is_active, role, can_moderate, can_run_pipeline, created_at)
            SELECT id, email, password_hash, is_active, 'admin', can_moderate, can_run_pipeline, created_at
            FROM staff_users
            """
        )
    )

    if "reader_users" in tables:
        bind.execute(
            sa.text(
                """
                INSERT INTO app_users (email, password_hash, is_active, role, can_moderate, can_run_pipeline, created_at)
                SELECT ru.email, ru.password_hash, ru.is_active, 'reader', 0, 0, ru.created_at
                FROM reader_users ru
                WHERE NOT EXISTS (SELECT 1 FROM app_users au WHERE au.email = ru.email)
                """
            )
        )

    if "staff_refresh_tokens" in tables:
        bind.execute(
            sa.text(
                """
                INSERT INTO app_refresh_tokens (user_id, token_hash, expires_at, created_at, revoked_at)
                SELECT staff_user_id, token_hash, expires_at, created_at, revoked_at
                FROM staff_refresh_tokens
                """
            )
        )

    if "reader_refresh_tokens" in tables and "reader_users" in tables:
        bind.execute(
            sa.text(
                """
                INSERT INTO app_refresh_tokens (user_id, token_hash, expires_at, created_at, revoked_at)
                SELECT au.id, rt.token_hash, rt.expires_at, rt.created_at, rt.revoked_at
                FROM reader_refresh_tokens rt
                JOIN reader_users ru ON ru.id = rt.reader_user_id
                JOIN app_users au ON au.email = ru.email
                """
            )
        )

    moderation_cols = (
        {c["name"] for c in inspector.get_columns("moderation_events")} if "moderation_events" in tables else set()
    )
    if "staff_user_id" in moderation_cols and "user_id" not in moderation_cols:
        with op.batch_alter_table("moderation_events", schema=None) as batch_op:
            batch_op.alter_column("staff_user_id", new_column_name="user_id")
            fk_names: list[str] = [
                fk["name"]
                for fk in inspector.get_foreign_keys("moderation_events")
                if "staff_user_id" in fk.get("constrained_columns", ())
            ]
            for name in fk_names:
                batch_op.drop_constraint(name, type_="foreignkey")
            batch_op.create_foreign_key(
                "fk_moderation_events_user_id",
                "app_users",
                ["user_id"],
                ["id"],
                ondelete="SET NULL",
            )

    for legacy in (
        "reader_refresh_tokens",
        "staff_refresh_tokens",
        "reader_users",
        "staff_users",
    ):
        if legacy in set(inspect(bind).get_table_names()):
            op.drop_table(legacy)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables: set[str] = set(inspector.get_table_names())

    if "app_users" not in tables:
        op.create_table(
            "app_users",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.Text(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("role", sa.String(length=32), nullable=False, server_default="reader"),
            sa.Column("can_moderate", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("can_run_pipeline", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_app_users_email", "app_users", ["email"], unique=True)

    if "app_refresh_tokens" not in tables:
        op.create_table(
            "app_refresh_tokens",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_app_refresh_tokens_user_id"), "app_refresh_tokens", ["user_id"])
        op.create_index(
            op.f("ix_app_refresh_tokens_token_hash"),
            "app_refresh_tokens",
            ["token_hash"],
            unique=True,
        )

    inspector = inspect(bind)
    _migrate_legacy_accounts(bind, inspector)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables: set[str] = set(inspector.get_table_names())

    if "moderation_events" in tables:
        cols = {c["name"] for c in inspector.get_columns("moderation_events")}
        if "user_id" in cols and "staff_users" in tables:
            with op.batch_alter_table("moderation_events", schema=None) as batch_op:
                fk_names: list[str] = [
                    fk["name"]
                    for fk in inspector.get_foreign_keys("moderation_events")
                    if "user_id" in fk.get("constrained_columns", ())
                ]
                for name in fk_names:
                    batch_op.drop_constraint(name, type_="foreignkey")
                batch_op.alter_column("user_id", new_column_name="staff_user_id")
                batch_op.create_foreign_key(
                    "fk_moderation_events_staff_user_id",
                    "staff_users",
                    ["staff_user_id"],
                    ["id"],
                    ondelete="SET NULL",
                )

    if "app_refresh_tokens" in tables:
        op.drop_table("app_refresh_tokens")
    if "app_users" in tables:
        op.drop_table("app_users")
