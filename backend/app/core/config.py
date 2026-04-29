from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "newsForGermanyRU-backend"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    database_url: str = "sqlite:///./news.db"
    rss_fetch_limit: int = 30
    rss_fetch_timeout_seconds: float = 30.0
    rss_max_response_bytes: int = 5_000_000
    rss_user_agent: str = "newsForGermanyRU/1.0 (+https://example.local)"
    auto_publish_threshold: float = 0.85
    # For hybrid publication: stricter than relevance filter; borderline items go to moderation queue.
    auto_publish_min_relevance: float = 0.5
    # When True, items merged into an existing story cluster are not auto published (duplicates / follow-ups).
    auto_publish_review_on_duplicate_cluster: bool = True
    # Comma-separated substrings; if any appear in title+summary, force moderation (case-insensitive).
    moderation_extra_review_keywords: str = ""

    llm_provider: Literal["stub", "openai"] = "stub"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    semantic_embedding_backend: str = "sentence_transformers"
    semantic_embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    semantic_relevance_min_score: float = 0.34
    semantic_dedup_min_similarity: float = 0.88
    semantic_dedup_lookback_days: int = 21

    # Comma-separated origins for browser clients (e.g. Vite dev server). Empty disables CORS middleware.
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"

    # In-process background RSS/pipeline (single-worker dev). Use external cron/beat for multi-replica.
    pipeline_scheduler_enabled: bool = False
    pipeline_interval_minutes: int = 30
    # Per-feed fetch attempts; exponential delay between attempts (base below).
    rss_feed_max_attempts: int = 3
    rss_feed_retry_base_delay_seconds: float = 0.5
    # One extra HTTP attempt on 429/5xx to OpenAI chat completions.
    openai_request_retries: int = 1
    # When the scheduled pipeline raises, the task can return a failure envelope instead of propagating.
    pipeline_task_swallow_errors: bool = True

    # One JSON object per log line on the root logger (production-friendly).
    log_json: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings: Settings = Settings()
