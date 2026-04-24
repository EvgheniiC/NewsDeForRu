"""Add clustered news schema and backfill.

Revision ID: 20260424_01
Revises:
Create Date: 2026-04-24
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

# revision identifiers, used by Alembic.
revision: str = "20260424_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_base_tables_if_missing() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("sources"):
        op.create_table(
            "sources",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("rss_url", sa.String(length=512), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("name", name="uq_sources_name"),
            sa.UniqueConstraint("rss_url", name="uq_sources_rss_url"),
        )
        op.create_index("ix_sources_id", "sources", ["id"])

    if not inspector.has_table("raw_news_items"):
        op.create_table(
            "raw_news_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("source_id", sa.Integer(), nullable=False),
            sa.Column("guid", sa.String(length=512), nullable=False),
            sa.Column("title", sa.String(length=512), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("url", sa.String(length=1024), nullable=False),
            sa.Column("published_at", sa.DateTime(), nullable=False),
            sa.Column("pipeline_status", sa.String(length=20), nullable=False, server_default="ingested"),
            sa.Column("relevance_score", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("relevance_reason", sa.String(length=256), nullable=False, server_default=""),
            sa.Column("cluster_key", sa.String(length=128), nullable=True),
            sa.Column("processed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
            sa.UniqueConstraint("source_id", "guid", name="uq_raw_news_source_guid"),
        )
        op.create_index("ix_raw_news_items_id", "raw_news_items", ["id"])
        op.create_index("ix_raw_news_items_guid", "raw_news_items", ["guid"])
        op.create_index("ix_raw_news_items_cluster_key", "raw_news_items", ["cluster_key"])

def _create_clusters_tables() -> None:
    op.create_table(
        "news_clusters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cluster_key", sa.String(length=128), nullable=False),
        sa.Column("canonical_title", sa.String(length=512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("centroid_hash", sa.String(length=128), nullable=True),
        sa.Column("size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("cluster_key", name="uq_news_clusters_cluster_key"),
    )
    op.create_index("ix_news_clusters_cluster_key", "news_clusters", ["cluster_key"])
    op.create_index("ix_news_clusters_updated_at", "news_clusters", ["updated_at"])

    op.create_table(
        "cluster_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("raw_item_id", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("similarity_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["cluster_id"], ["news_clusters.id"]),
        sa.ForeignKeyConstraint(["raw_item_id"], ["raw_news_items.id"]),
        sa.UniqueConstraint("cluster_id", "raw_item_id", name="uq_cluster_item_pair"),
        sa.UniqueConstraint("raw_item_id", name="uq_cluster_item_raw"),
    )
    op.create_index("ix_cluster_items_cluster_id", "cluster_items", ["cluster_id"])
    op.create_index("ix_cluster_items_raw_item_id", "cluster_items", ["raw_item_id"])
    op.create_index("ix_cluster_items_cluster_id_is_primary", "cluster_items", ["cluster_id", "is_primary"])


def _create_processed_news_if_missing() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("processed_news"):
        return

    op.create_table(
        "processed_news",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("raw_item_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("one_sentence_summary", sa.Text(), nullable=False),
        sa.Column("plain_language", sa.Text(), nullable=False),
        sa.Column("impact_owner", sa.Text(), nullable=False),
        sa.Column("impact_tenant", sa.Text(), nullable=False),
        sa.Column("impact_buyer", sa.Text(), nullable=False),
        sa.Column("action_items", sa.Text(), nullable=False),
        sa.Column("bonus_block", sa.Text(), nullable=False, server_default=""),
        sa.Column("spoiler", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_url", sa.String(length=1024), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("cluster_id", sa.Integer(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("publication_status", sa.String(length=20), nullable=False, server_default="needs_review"),
        sa.Column("read_time_minutes", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["raw_item_id"], ["raw_news_items.id"]),
        sa.ForeignKeyConstraint(["cluster_id"], ["news_clusters.id"]),
        sa.UniqueConstraint("raw_item_id", name="uq_processed_news_raw_item_id"),
    )
    op.create_index("ix_processed_news_id", "processed_news", ["id"])
    op.create_index("ix_processed_news_cluster_id", "processed_news", ["cluster_id"])
    op.create_index(
        "ix_processed_news_publication_status_created_at",
        "processed_news",
        ["publication_status", "created_at"],
    )


def _alter_existing_tables() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("raw_news_items"):
        raw_columns: set[str] = {column["name"] for column in inspector.get_columns("raw_news_items")}
        raw_uniques: set[str] = {constraint["name"] for constraint in inspector.get_unique_constraints("raw_news_items")}
        raw_indexes: set[str] = {index["name"] for index in inspector.get_indexes("raw_news_items")}
        with op.batch_alter_table("raw_news_items") as batch_op:
            if "processed_at" not in raw_columns:
                batch_op.add_column(sa.Column("processed_at", sa.DateTime(), nullable=True))
            if "uq_raw_news_source_guid" not in raw_uniques and "uq_raw_news_source_guid" not in raw_indexes:
                batch_op.create_unique_constraint("uq_raw_news_source_guid", ["source_id", "guid"])

    if inspector.has_table("processed_news"):
        processed_columns: set[str] = {column["name"] for column in inspector.get_columns("processed_news")}
        processed_fks: set[str] = {
            foreign_key["name"] for foreign_key in inspector.get_foreign_keys("processed_news") if foreign_key["name"]
        }
        processed_indexes: set[str] = {index["name"] for index in inspector.get_indexes("processed_news")}
        with op.batch_alter_table("processed_news") as batch_op:
            if "cluster_id" not in processed_columns:
                batch_op.add_column(sa.Column("cluster_id", sa.Integer(), nullable=True))
            if "version" not in processed_columns:
                batch_op.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
            if "fk_processed_news_cluster_id" not in processed_fks:
                batch_op.create_foreign_key("fk_processed_news_cluster_id", "news_clusters", ["cluster_id"], ["id"])
            if "ix_processed_news_publication_status_created_at" not in processed_indexes:
                batch_op.create_index(
                    "ix_processed_news_publication_status_created_at",
                    ["publication_status", "created_at"],
                )


def _backfill_clusters() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        text(
            "SELECT id, title, summary, cluster_key "
            "FROM raw_news_items "
            "WHERE cluster_key IS NOT NULL AND cluster_key <> ''"
        )
    ).mappings()

    for row in rows:
        cluster_key: str = str(row["cluster_key"])
        cluster = bind.execute(
            text("SELECT id FROM news_clusters WHERE cluster_key = :cluster_key"),
            {"cluster_key": cluster_key},
        ).mappings().first()

        if cluster is None:
            bind.execute(
                text(
                    "INSERT INTO news_clusters (cluster_key, canonical_title, summary, size, created_at, updated_at) "
                    "VALUES (:cluster_key, :canonical_title, :summary, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                ),
                {
                    "cluster_key": cluster_key,
                    "canonical_title": str(row["title"])[:512],
                    "summary": str(row["summary"]),
                },
            )
            cluster = bind.execute(
                text("SELECT id FROM news_clusters WHERE cluster_key = :cluster_key"),
                {"cluster_key": cluster_key},
            ).mappings().first()

        if cluster is None:
            continue

        existing_cluster_item = bind.execute(
            text("SELECT 1 FROM cluster_items WHERE raw_item_id = :raw_item_id"),
            {"raw_item_id": int(row["id"])},
        ).first()
        if existing_cluster_item is None:
            bind.execute(
                text(
                    "INSERT INTO cluster_items (cluster_id, raw_item_id, is_primary, similarity_score, created_at) "
                    "VALUES (:cluster_id, :raw_item_id, false, 1.0, CURRENT_TIMESTAMP)"
                ),
                {"cluster_id": int(cluster["id"]), "raw_item_id": int(row["id"])},
            )
        bind.execute(
            text("UPDATE processed_news SET cluster_id = :cluster_id WHERE raw_item_id = :raw_item_id"),
            {"cluster_id": int(cluster["id"]), "raw_item_id": int(row["id"])},
        )

    cluster_rows = bind.execute(text("SELECT id FROM news_clusters")).mappings()
    for cluster_row in cluster_rows:
        cluster_id: int = int(cluster_row["id"])
        bind.execute(
            text(
                "UPDATE cluster_items SET is_primary = CASE "
                "WHEN raw_item_id = (SELECT MIN(raw_item_id) FROM cluster_items ci WHERE ci.cluster_id = :cluster_id) "
                "THEN 1 ELSE 0 END "
                "WHERE cluster_id = :cluster_id"
            ),
            {"cluster_id": cluster_id},
        )
        bind.execute(
            text(
                "UPDATE news_clusters SET size = ("
                "SELECT COUNT(1) FROM cluster_items WHERE cluster_id = :cluster_id"
                "), updated_at = CURRENT_TIMESTAMP WHERE id = :cluster_id"
            ),
            {"cluster_id": cluster_id},
        )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    _create_base_tables_if_missing()

    if not inspector.has_table("news_clusters") and not inspector.has_table("cluster_items"):
        _create_clusters_tables()
    _create_processed_news_if_missing()

    _alter_existing_tables()
    _backfill_clusters()


def downgrade() -> None:
    with op.batch_alter_table("processed_news") as batch_op:
        batch_op.drop_index("ix_processed_news_publication_status_created_at")
        batch_op.drop_constraint("fk_processed_news_cluster_id", type_="foreignkey")
        batch_op.drop_column("version")
        batch_op.drop_column("cluster_id")

    with op.batch_alter_table("raw_news_items") as batch_op:
        batch_op.drop_constraint("uq_raw_news_source_guid", type_="unique")
        batch_op.drop_column("processed_at")

    op.drop_index("ix_cluster_items_cluster_id_is_primary", table_name="cluster_items")
    op.drop_index("ix_cluster_items_raw_item_id", table_name="cluster_items")
    op.drop_index("ix_cluster_items_cluster_id", table_name="cluster_items")
    op.drop_table("cluster_items")

    op.drop_index("ix_news_clusters_updated_at", table_name="news_clusters")
    op.drop_index("ix_news_clusters_cluster_key", table_name="news_clusters")
    op.drop_table("news_clusters")
