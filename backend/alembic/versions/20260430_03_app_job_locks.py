"""app_job_locks for Telegram digest mutual exclusion on SQLite."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260430_03"
down_revision: str | None = "20260430_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables: set[str] = set(inspector.get_table_names())
    if "app_job_locks" not in tables:
        op.create_table(
            "app_job_locks",
            sa.Column("job_key", sa.String(length=64), nullable=False),
            sa.Column("locked_until", sa.DateTime(), nullable=True),
            sa.Column("holder", sa.String(length=128), nullable=False, server_default=""),
            sa.PrimaryKeyConstraint("job_key"),
        )
        op.execute(
            sa.text(
                "INSERT INTO app_job_locks (job_key, locked_until, holder) "
                "VALUES ('telegram_digest', NULL, '')"
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "app_job_locks" in inspector.get_table_names():
        op.drop_table("app_job_locks")
