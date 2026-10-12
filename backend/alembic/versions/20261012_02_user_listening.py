"""Per-account listen queue and playback progress."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20261012_02"
down_revision: str | None = "20261012_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names: set[str] = set(inspector.get_table_names())
    if "app_users" not in table_names:
        return
    if "user_listening_states" in table_names:
        return
    op.create_table(
        "user_listening_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("state_json", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_listening_states_user_id"),
    )
    op.create_index("ix_user_listening_states_user_id", "user_listening_states", ["user_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table_names: set[str] = set(inspector.get_table_names())
    if "user_listening_states" not in table_names:
        return
    op.drop_index("ix_user_listening_states_user_id", table_name="user_listening_states")
    op.drop_table("user_listening_states")
