"""Store one row per unique Android app install."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20261012_01"
down_revision: str | None = "20261006_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "app_installs" in set(inspector.get_table_names()):
        return
    op.create_table(
        "app_installs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("install_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("install_id", name="uq_app_installs_install_id"),
    )
    op.create_index("ix_app_installs_id", "app_installs", ["id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "app_installs" not in set(inspector.get_table_names()):
        return
    op.drop_index("ix_app_installs_id", table_name="app_installs")
    op.drop_table("app_installs")
