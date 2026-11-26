"""Remember whether a visit came from the website or the Android app."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20261126_01"
down_revision: str | None = "20261020_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn: sa.engine.Connection = op.get_bind()
    inspector = inspect(conn)
    if "app_visits" not in inspector.get_table_names():
        return
    columns: set[str] = {column["name"] for column in inspector.get_columns("app_visits")}
    if "surface" in columns:
        return
    with op.batch_alter_table("app_visits") as batch_op:
        batch_op.add_column(sa.Column("surface", sa.String(length=16), nullable=True))


def downgrade() -> None:
    conn: sa.engine.Connection = op.get_bind()
    inspector = inspect(conn)
    if "app_visits" not in inspector.get_table_names():
        return
    columns: set[str] = {column["name"] for column in inspector.get_columns("app_visits")}
    if "surface" not in columns:
        return
    with op.batch_alter_table("app_visits") as batch_op:
        batch_op.drop_column("surface")
