"""Staff operator accounts, refresh tokens, moderation audit FK."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260515_01"
down_revision: str | None = "20260430_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables: set[str] = set(inspector.get_table_names())
    if "staff_users" not in tables:
        op.create_table(
            "staff_users",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.Text(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("can_moderate", sa.Boolean(), nullable=False),
            sa.Column("can_run_pipeline", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_staff_users_email", "staff_users", ["email"], unique=True)
    if "staff_refresh_tokens" not in tables:
        op.create_table(
            "staff_refresh_tokens",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("staff_user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["staff_user_id"], ["staff_users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_staff_refresh_tokens_staff_user_id"), "staff_refresh_tokens", ["staff_user_id"])
        op.create_index(
            op.f("ix_staff_refresh_tokens_token_hash"), "staff_refresh_tokens", ["token_hash"], unique=True
        )

    moderation_cols = {c["name"] for c in inspector.get_columns("moderation_events")} if "moderation_events" in tables else set()
    if "staff_user_id" not in moderation_cols:
        # SQLite cannot ALTER TABLE ADD CONSTRAINT; batch mode rebuilds the table.
        with op.batch_alter_table("moderation_events", schema=None) as batch_op:
            batch_op.add_column(sa.Column("staff_user_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_moderation_events_staff_user_id",
                "staff_users",
                ["staff_user_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch_op.create_index(op.f("ix_moderation_events_staff_user_id"), ["staff_user_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "moderation_events" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("moderation_events")}
        if "staff_user_id" in cols:
            fk_names: list[str] = [
                fk["name"]
                for fk in inspector.get_foreign_keys("moderation_events")
                if "staff_user_id" in fk.get("constrained_columns", ())
            ]
            index_names: list[str] = [
                ixdef["name"]
                for ixdef in inspector.get_indexes("moderation_events")
                if ixdef.get("column_names") == ["staff_user_id"]
            ]
            with op.batch_alter_table("moderation_events", schema=None) as batch_op:
                for ix_name in index_names:
                    batch_op.drop_index(ix_name)
                for name in fk_names:
                    batch_op.drop_constraint(name, type_="foreignkey")
                batch_op.drop_column("staff_user_id")

    if "staff_refresh_tokens" in inspector.get_table_names():
        op.drop_table("staff_refresh_tokens")
    if "staff_users" in inspector.get_table_names():
        op.drop_table("staff_users")
