"""Store one app visit per session and Berlin calendar day."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20261006_01"
down_revision: str | None = "20261004_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "app_visits" in set(inspector.get_table_names()):
        return
    op.create_table(
        "app_visits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("session_id", "visit_date", name="uq_app_visits_session_day"),
    )
    op.create_index("ix_app_visits_visit_date", "app_visits", ["visit_date"])
    op.create_index("ix_app_visits_id", "app_visits", ["id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "app_visits" not in set(inspector.get_table_names()):
        return
    op.drop_index("ix_app_visits_id", table_name="app_visits")
    op.drop_index("ix_app_visits_visit_date", table_name="app_visits")
    op.drop_table("app_visits")
