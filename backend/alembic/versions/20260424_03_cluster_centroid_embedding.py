"""Store semantic cluster centroid embeddings as JSON.

Revision ID: 20260424_03
Revises: 20260424_02
Create Date: 2026-04-24
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260424_03"
down_revision: str | None = "20260424_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("news_clusters"):
        return
    columns: set[str] = {column["name"] for column in inspector.get_columns("news_clusters")}
    if "centroid_embedding_json" not in columns:
        op.add_column("news_clusters", sa.Column("centroid_embedding_json", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("news_clusters"):
        return
    columns: set[str] = {column["name"] for column in inspector.get_columns("news_clusters")}
    if "centroid_embedding_json" in columns:
        with op.batch_alter_table("news_clusters") as batch_op:
            batch_op.drop_column("centroid_embedding_json")
