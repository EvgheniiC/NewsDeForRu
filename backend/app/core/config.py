from typing import Literal, Self

from pydantic import Field, model_validator
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
    # Cron: run at minute :00 for each clock hour from start through end (inclusive), local to timezone below.
    pipeline_schedule_start_hour: int = Field(default=6, ge=0, le=23)
    pipeline_schedule_end_hour: int = Field(default=22, ge=0, le=23)
    pipeline_schedule_timezone: str = "Europe/Berlin"
    # Per-feed fetch attempts; exponential delay between attempts (base below).
    rss_feed_max_attempts: int = 3
    rss_feed_retry_base_delay_seconds: float = 0.5
    # One extra HTTP attempt on 429/5xx to OpenAI chat completions.
    openai_request_retries: int = 1
    # When the scheduled pipeline raises, the task can return a failure envelope instead of propagating.
    pipeline_task_swallow_errors: bool = True

    # One JSON object per log line on the root logger (production-friendly).
    log_json: bool = False
    # Text logs include run_id prefix when pipeline context is active (ignored when log_json=true).
    log_prefix_run_id_plain: bool = True

    # Optional error tracking for production (empty = disabled).
    sentry_dsn: str = ""

    # Expose Prometheus text metrics at GET /metrics (single-process; disable behind auth in prod).
    prometheus_metrics_enabled: bool = False

    # Read-only provenance routes (GET /internal/provenance/*). Empty = routes return 404.
    provenance_api_key: str = ""

    # Telegram Bot API (optional): autopublish in pipeline + immediate send when a moderator approves queue items.
    telegram_notifications_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def pipeline_schedule_hours_ordered(self) -> Self:
        if self.pipeline_schedule_start_hour > self.pipeline_schedule_end_hour:
            raise ValueError(
                "pipeline_schedule_start_hour must be <= pipeline_schedule_end_hour "
                "(same calendar day window)"
            )
        return self


settings: Settings = Settings()
