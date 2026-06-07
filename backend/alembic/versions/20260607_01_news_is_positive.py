"""Add is_positive to processed_news for the TPN (positive-only) app feed tab."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260607_01"
down_revision: str | None = "20260605_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn: sa.engine.Connection = op.get_bind()
    insp = inspect(conn)
    if "processed_news" not in insp.get_table_names():
        return
    cols: set[str] = {c["name"] for c in insp.get_columns("processed_news")}
    with op.batch_alter_table("processed_news") as batch_op:
        if "is_positive" not in cols:
            batch_op.add_column(
                sa.Column(
                    "is_positive",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.text("false"),
                ),
            )


def downgrade() -> None:
    conn: sa.engine.Connection = op.get_bind()
    insp = inspect(conn)
    if "processed_news" not in insp.get_table_names():
        return
    cols: set[str] = {c["name"] for c in insp.get_columns("processed_news")}
    with op.batch_alter_table("processed_news") as batch_op:
        if "is_positive" in cols:
            batch_op.drop_column("is_positive")
