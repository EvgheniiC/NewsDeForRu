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

    semantic_embedding_backend: str = "sentence_transformers"
    semantic_embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    semantic_relevance_min_score: float = 0.34
    semantic_dedup_min_similarity: float = 0.88
    semantic_dedup_lookback_days: int = 21

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings: Settings = Settings()
