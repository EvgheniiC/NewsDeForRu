"""Add immutable legal attribution metadata for open sources."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260802_02"
down_revision: str | None = "20260802_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("default_licence", sa.String(length=128), nullable=True))
    op.add_column("sources", sa.Column("default_licence_url", sa.String(length=1024), nullable=True))
    op.add_column("sources", sa.Column("copyright_holder", sa.String(length=256), nullable=True))
    op.add_column("sources", sa.Column("original_language", sa.String(length=16), nullable=True))
    op.add_column("sources", sa.Column("changes_notice", sa.Text(), nullable=True))
    op.add_column(
        "sources",
        sa.Column("rights_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "sources",
        sa.Column("text_only", sa.Boolean(), server_default=sa.true(), nullable=False),
    )

    op.add_column("raw_news_items", sa.Column("original_language", sa.String(length=16), nullable=True))
    op.add_column(
        "raw_news_items",
        sa.Column("retrieved_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.add_column("raw_news_items", sa.Column("licence", sa.String(length=128), nullable=True))
    op.add_column("raw_news_items", sa.Column("licence_url", sa.String(length=1024), nullable=True))
    op.add_column("raw_news_items", sa.Column("copyright_holder", sa.String(length=256), nullable=True))
    op.add_column(
        "raw_news_items",
        sa.Column("is_translated", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column(
        "raw_news_items",
        sa.Column("is_ai_summarised", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column("raw_news_items", sa.Column("changes_notice", sa.Text(), nullable=True))
    op.add_column(
        "raw_news_items",
        sa.Column(
            "third_party_material_excluded",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )
    op.add_column("raw_news_items", sa.Column("source_revision", sa.String(length=256), nullable=True))
    op.add_column(
        "raw_news_items",
        sa.Column("rights_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
    )

    op.add_column("processed_news", sa.Column("original_title", sa.String(length=512), nullable=True))
    op.add_column("processed_news", sa.Column("original_language", sa.String(length=16), nullable=True))
    op.add_column("processed_news", sa.Column("retrieved_at", sa.DateTime(), nullable=True))
    op.add_column("processed_news", sa.Column("licence", sa.String(length=128), nullable=True))
    op.add_column("processed_news", sa.Column("licence_url", sa.String(length=1024), nullable=True))
    op.add_column("processed_news", sa.Column("copyright_holder", sa.String(length=256), nullable=True))
    op.add_column(
        "processed_news",
        sa.Column("is_translated", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column(
        "processed_news",
        sa.Column("is_ai_summarised", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column("processed_news", sa.Column("changes_notice", sa.Text(), nullable=True))
    op.add_column(
        "processed_news",
        sa.Column(
            "third_party_material_excluded",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )
    op.add_column("processed_news", sa.Column("source_revision", sa.String(length=256), nullable=True))
    op.add_column(
        "processed_news",
        sa.Column("rights_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    for column_name in (
        "rights_verified",
        "source_revision",
        "third_party_material_excluded",
        "changes_notice",
        "is_ai_summarised",
        "is_translated",
        "copyright_holder",
        "licence_url",
        "licence",
        "retrieved_at",
        "original_language",
        "original_title",
    ):
        op.drop_column("processed_news", column_name)
    for column_name in (
        "rights_verified",
        "source_revision",
        "third_party_material_excluded",
        "changes_notice",
        "is_ai_summarised",
        "is_translated",
        "copyright_holder",
        "licence_url",
        "licence",
        "retrieved_at",
        "original_language",
    ):
        op.drop_column("raw_news_items", column_name)
    for column_name in (
        "text_only",
        "rights_verified",
        "changes_notice",
        "original_language",
        "copyright_holder",
        "default_licence_url",
        "default_licence",
    ):
        op.drop_column("sources", column_name)
