"""PostgreSQL migration integration test.

In CI (GitHub Actions), Postgres runs as a job service; set MIGRATION_TEST_ADMIN_URL to the
admin connection (database `postgres`) so the test can CREATE/DROP ephemeral databases.
Locally, defaults match docker compose (port 55432) unless MIGRATION_TEST_ADMIN_URL is set.
"""

from __future__ import annotations

import os
import subprocess
import uuid
from collections.abc import Generator
from pathlib import Path

import psycopg
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine, make_url


PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
BACKEND_ROOT: Path = PROJECT_ROOT / "backend"


def _build_test_database_url(admin_url: str, database_name: str) -> str:
    return make_url(admin_url).set(database=database_name).render_as_string(hide_password=False)


def _to_psycopg_url(sqlalchemy_url: str) -> str:
    return sqlalchemy_url.replace("postgresql+psycopg://", "postgresql://", 1)


def _admin_database_url() -> str:
    return os.getenv(
        "MIGRATION_TEST_ADMIN_URL",
        "postgresql+psycopg://news:news@127.0.0.1:55432/postgres",
    )


@pytest.fixture()
def postgres_test_db_url() -> Generator[str, None, None]:
    admin_url: str = _admin_database_url()
    unique_db_name: str = f"news_migration_test_{uuid.uuid4().hex[:8]}"
    target_url: str = _build_test_database_url(admin_url, unique_db_name)

    psycopg_admin_url: str = _to_psycopg_url(admin_url)
    with psycopg.connect(psycopg_admin_url, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'CREATE DATABASE "{unique_db_name}"')

    try:
        yield target_url
    finally:
        with psycopg.connect(psycopg_admin_url, autocommit=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_terminate_backend(pid) "
                    "FROM pg_stat_activity "
                    "WHERE datname = %s AND pid <> pg_backend_pid()",
                    (unique_db_name,),
                )
                cursor.execute(f'DROP DATABASE IF EXISTS "{unique_db_name}"')


def test_alembic_upgrade_creates_expected_schema(postgres_test_db_url: str) -> None:
    env: dict[str, str] = {**os.environ, "DATABASE_URL": postgres_test_db_url}
    result: subprocess.CompletedProcess[str] = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    engine: Engine = create_engine(postgres_test_db_url, future=True)
    try:
        inspector = inspect(engine)
        table_names: set[str] = set(inspector.get_table_names())
        assert {
            "sources",
            "raw_news_items",
            "processed_news",
            "news_clusters",
            "cluster_items",
            "moderation_events",
        } <= table_names

        raw_columns: set[str] = {column["name"] for column in inspector.get_columns("raw_news_items")}
        processed_columns: set[str] = {column["name"] for column in inspector.get_columns("processed_news")}
        cluster_item_columns: set[str] = {column["name"] for column in inspector.get_columns("cluster_items")}
        cluster_columns: set[str] = {column["name"] for column in inspector.get_columns("news_clusters")}

        assert {"guid", "pipeline_status", "cluster_key", "processed_at"} <= raw_columns
        assert {
            "raw_item_id",
            "cluster_id",
            "version",
            "publication_status",
            "topic",
            "is_urgent",
            "impact_presentation",
            "impact_unified",
        } <= processed_columns
        assert {"cluster_id", "raw_item_id", "is_primary", "similarity_score"} <= cluster_item_columns
        assert "centroid_embedding_json" in cluster_columns

        source_columns: set[str] = {column["name"] for column in inspector.get_columns("sources")}
        assert {"source_key", "name", "rss_url"} <= source_columns

        with engine.connect() as connection:
            version_rows = connection.execute(text("SELECT version_num FROM alembic_version")).all()
        assert len(version_rows) == 1
        assert version_rows[0][0] == "20260428_01"

        engagement_columns: set[str] = {column["name"] for column in inspector.get_columns("user_engagement_events")}
        assert {"anonymous_user_id", "processed_news_id", "event_type", "payload_json", "client_event_id"} <= engagement_columns
    finally:
        engine.dispose()
