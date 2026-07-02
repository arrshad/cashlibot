"""Environment-driven settings + paths to YAML config files."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BACKEND_DIR / "config"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None,  # values come from container env (compose loads `.env` itself)
        extra="ignore",
        case_sensitive=False,
    )

    # Telegram
    telegram_bot_token: str = ""
    telegram_bot_username: str = ""

    # Postgres
    postgres_user: str = "cashlibot"
    postgres_password: str = ""
    postgres_db: str = "cashlibot"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0

    # App
    log_level: str = "info"
    admin_jwt_secret: str = ""

    # AI providers (only required if you use a provider that needs them)
    deepseek_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Frontend URLs
    miniapp_url: str = ""
    admin_url: str = ""

    # Migration toggle for entrypoint scripts
    run_migrations: bool = Field(default=False)

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
