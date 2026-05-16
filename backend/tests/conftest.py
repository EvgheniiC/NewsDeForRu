"""Pytest defaults: fast deterministic embeddings without downloading models."""

from __future__ import annotations

import os

# Isolate from developer .env (e.g. HTTP_VERIFY_SSL=false breaks httpx verify assertions).
os.environ["HTTP_VERIFY_SSL"] = "true"
os.environ.pop("HTTP_CA_BUNDLE_PATH", None)
os.environ.pop("TELEGRAM_HTTP_CA_BUNDLE_PATH", None)
os.environ.pop("TELEGRAM_HTTP_VERIFY_SSL", None)

# Isolated DB for tests (avoids schema drift vs a dev sqlite file on disk).
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "integration-test-secret-must-be-32-characters-min!!")
os.environ.setdefault("SEMANTIC_EMBEDDING_BACKEND", "hash")
os.environ.setdefault("SEMANTIC_RELEVANCE_MIN_SCORE", "0.12")
os.environ.setdefault("SEMANTIC_DEDUP_MIN_SIMILARITY", "0.99")
os.environ.setdefault("PIPELINE_SCHEDULER_ENABLED", "false")
os.environ.setdefault("RSS_FEED_RETRY_BASE_DELAY_SECONDS", "0")
