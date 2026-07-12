from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    app_env: str = "development"
    app_name: str = "python-chat-system"
    database_url: str = "sqlite+aiosqlite:///./data/database/chat_system.db"
    secret_key: str = "change-this-key"
    settings_cache_ttl_seconds: int = 5
    max_active_generations: int = 1
    max_queue_length: int = 16
    gpu_memory_limit_mb: int = 11000
    ram_memory_limit_mb: int = 24000
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cors_allow_origin_regex: str | None = r"^https?://.+$"
    cors_allow_credentials: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    return AppConfig()
