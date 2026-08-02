from typing import Literal, Self

from pydantic import AliasChoices, Field, model_validator
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
    # Fail closed: add a source key only after its production usage is approved.
    rss_enabled_source_keys: str = ""
    auto_publish_threshold: float = 0.85
    # For hybrid publication: stricter than relevance filter; borderline items go to moderation queue.
    auto_publish_min_relevance: float = 0.5
    # When True, items merged into an existing story cluster are not auto published (duplicates / follow-ups).
    auto_publish_review_on_duplicate_cluster: bool = True
    # Comma-separated substrings; if any appear in title+summary, force moderation (case-insensitive).
    moderation_extra_review_keywords: str = ""
    # Technical safeguards only; these values are not legally safe quotation limits.
    publisher_text_overlap_min_words: int = Field(default=8, ge=3, le=50)
    publisher_text_overlap_min_chars: int = Field(default=50, ge=20, le=500)
    publisher_text_similarity_min_chars: int = Field(default=40, ge=20, le=500)
    publisher_text_similarity_threshold: float = Field(default=0.72, ge=0.5, le=1.0)

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
    # Include https://localhost for Capacitor Android WebView (androidScheme https).
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173,http://localhost,https://localhost"

    # In-process background RSS/pipeline (single-worker dev). Use external cron/beat for multi-replica.
    pipeline_scheduler_enabled: bool = False
    # Cron: run at minute :00 for each clock hour from start through end (inclusive), local to timezone below.
    pipeline_schedule_start_hour: int = Field(default=6, ge=0, le=23)
    pipeline_schedule_end_hour: int = Field(default=22, ge=0, le=23)
    pipeline_schedule_timezone: str = "Europe/Berlin"
    # Per-feed fetch attempts; exponential delay between attempts (base below).
    rss_feed_max_attempts: int = 3
    rss_feed_retry_base_delay_seconds: float = 0.5
    # Outbound HTTPS (RSS, OpenAI, Telegram, og:image): PEM bundle or verify toggle.
    # Alias TELEGRAM_HTTP_* kept for backward-compatible .env files.
    http_ca_bundle_path: str = Field(
        default="",
        validation_alias=AliasChoices(
            "http_ca_bundle_path",
            "HTTP_CA_BUNDLE_PATH",
            "TELEGRAM_HTTP_CA_BUNDLE_PATH",
        ),
    )
    http_verify_ssl: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "http_verify_ssl",
            "HTTP_VERIFY_SSL",
            "TELEGRAM_HTTP_VERIFY_SSL",
        ),
    )
    # When RSS has no image, optionally GET article HTML and parse og:image (extra latency per item).
    og_image_fetch_enabled: bool = False
    og_image_fetch_timeout_seconds: float = 12.0
    og_image_max_response_bytes: int = 2_000_000
    # One extra HTTP attempt on 429/5xx to OpenAI chat completions.
    openai_request_retries: int = 1
    # When the scheduled pipeline raises, the task can return a failure envelope instead of propagating.
    pipeline_task_swallow_errors: bool = True

    # Daily check: publisher article URLs for published news in the last N Berlin calendar days.
    source_url_check_scheduler_enabled: bool = False
    source_url_check_hour: int = Field(default=4, ge=0, le=23)
    source_url_check_timezone: str = "Europe/Berlin"
    source_url_check_lookback_days: int = Field(default=3, ge=1, le=14)
    source_url_check_timeout_seconds: float = Field(default=8.0, ge=2.0, le=60.0)
    source_url_check_max_items: int = Field(default=500, ge=10, le=5000)
    source_url_check_lock_ttl_seconds: int = Field(default=1800, ge=60, le=7200)

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

    # Operator auth (JWT access + opaque refresh). Use a strong secret in production.
    jwt_secret_key: str = "development-only-change-in-production-min-32-chars!!"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = Field(default=30, ge=5, le=24 * 60)
    jwt_refresh_expire_days: int = Field(default=14, ge=1, le=365)

    # Password reset (email link). Requires SMTP for delivery in production.
    password_reset_enabled: bool = True
    password_reset_expire_minutes: int = Field(default=60, ge=15, le=24 * 60)
    # Frontend origin for links in email (e.g. https://simplenewsapp.de). Falls back to PUBLIC_APP_BASE_URL.
    password_reset_frontend_base_url: str = ""
    # Development only: return reset link in API when SMTP is off (never enable in production).
    password_reset_dev_expose_link: bool = False

    # Email verification after reader registration (requires SMTP in production).
    email_verification_enabled: bool = True
    email_verification_expire_minutes: int = Field(default=24 * 60, ge=15, le=7 * 24 * 60)
    # Development only: return verification link in API when SMTP is off (never enable in production).
    email_verification_dev_expose_link: bool = False

    support_contact_email: str = ""
    feedback_rate_limit_max_per_hour: int = Field(default=5, ge=1, le=100)
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True

    # Telegram Bot API (optional): autopublish in pipeline + immediate send when a moderator approves queue items.
    telegram_notifications_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    # Public web app URL for deep links (e.g. https://app.example.com). Adds “Читать в приложении” in Telegram.
    public_app_base_url: str = ""
    # Scheduled digest: Europe/Berlin hours (comma-separated). Auto-published, importance >= min, non-urgent only.
    telegram_digest_scheduler_enabled: bool = True
    telegram_digest_hours: str = "7,15,20"
    telegram_digest_timezone: str = "Europe/Berlin"
    telegram_digest_min_importance: int = Field(default=6, ge=1, le=10)
    telegram_digest_max_per_slot: int = Field(default=3, ge=1, le=10)
    # Fetch up to this many rows before deduping by news cluster for digest (see TODO: aging/fairness).
    telegram_digest_candidate_scan_limit: int = Field(default=120, ge=20, le=2000)
    # Breaking (urgent) auto-publish: retries with exponential backoff on full delivery failure.
    telegram_urgent_send_max_attempts: int = Field(default=3, ge=1, le=10)
    telegram_urgent_send_retry_base_seconds: float = Field(default=30.0, ge=0.0, le=3600.0)
    # When True, urgent Telegram sends run in a daemon thread so the RSS pipeline loop is not blocked by retries.
    telegram_urgent_background_enabled: bool = False
    # Moderation approve / digest HTTP delivery retries (independent of urgent breaking-news retries).
    telegram_moderation_send_max_attempts: int = Field(default=3, ge=1, le=10)
    telegram_moderation_send_retry_base_seconds: float = Field(default=5.0, ge=0.0, le=600.0)
    telegram_digest_send_max_attempts: int = Field(default=3, ge=1, le=10)
    telegram_digest_send_retry_base_seconds: float = Field(default=5.0, ge=0.0, le=600.0)
    # SQLite / generic DB: TTL for digest mutex row; release() clears it when the job finishes.
    telegram_digest_lock_ttl_seconds: int = Field(default=600, ge=30, le=3600)

    # FCM push (Android): urgent / breaking news only. Requires Firebase service account JSON on the server.
    push_notifications_enabled: bool = False
    fcm_service_account_path: str = ""
    fcm_urgent_topic: str = "urgent-news"
    push_urgent_send_max_attempts: int = Field(default=3, ge=1, le=10)
    push_urgent_send_retry_base_seconds: float = Field(default=5.0, ge=0.0, le=600.0)
    # When True, urgent push runs in a daemon thread so the RSS pipeline loop is not blocked by retries/sleep.
    push_urgent_background_enabled: bool = False

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

    @model_validator(mode="after")
    def jwt_secret_required_in_production(self) -> Self:
        if self.app_env.strip().lower() == "production" and not self.jwt_secret_key.strip():
            raise ValueError("JWT_SECRET_KEY is required when APP_ENV=production")
        if len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return self


settings: Settings = Settings()
