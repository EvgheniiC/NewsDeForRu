"""Add topic and is_urgent to processed_news."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260427_01"
down_revision: str | None = "20260424_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn: sa.engine.Connection = op.get_bind()
    insp = inspect(conn)
    if "processed_news" not in insp.get_table_names():
        return
    cols: set[str] = {c["name"] for c in insp.get_columns("processed_news")}
    with op.batch_alter_table("processed_news") as batch_op:
        if "topic" not in cols:
            batch_op.add_column(
                sa.Column(
                    "topic",
                    sa.String(length=32),
                    nullable=False,
                    server_default="life",
                ),
            )
        if "is_urgent" not in cols:
            batch_op.add_column(
                sa.Column(
                    "is_urgent",
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
        if "is_urgent" in cols:
            batch_op.drop_column("is_urgent")
        if "topic" in cols:
            batch_op.drop_column("topic")
