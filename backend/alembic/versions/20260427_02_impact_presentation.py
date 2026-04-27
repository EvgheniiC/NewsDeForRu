"""Add impact_presentation and impact_unified to processed_news."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260427_02"
down_revision: str | None = "20260427_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn: sa.engine.Connection = op.get_bind()
    insp = inspect(conn)
    if "processed_news" not in insp.get_table_names():
        return
    cols: set[str] = {c["name"] for c in insp.get_columns("processed_news")}
    with op.batch_alter_table("processed_news") as batch_op:
        if "impact_presentation" not in cols:
            batch_op.add_column(
                sa.Column(
                    "impact_presentation",
                    sa.String(length=16),
                    nullable=False,
                    server_default="multi",
                ),
            )
        if "impact_unified" not in cols:
            batch_op.add_column(
                sa.Column("impact_unified", sa.Text(), nullable=False, server_default=""),
            )


def downgrade() -> None:
    conn: sa.engine.Connection = op.get_bind()
    insp = inspect(conn)
    if "processed_news" not in insp.get_table_names():
        return
    cols: set[str] = {c["name"] for c in insp.get_columns("processed_news")}
    with op.batch_alter_table("processed_news") as batch_op:
        if "impact_unified" in cols:
            batch_op.drop_column("impact_unified")
        if "impact_presentation" in cols:
            batch_op.drop_column("impact_presentation")
