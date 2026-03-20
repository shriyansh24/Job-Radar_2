from __future__ import annotations

import warnings

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="JR_")

    # App
    app_name: str = "JobRadar V2"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # Auth
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database
    database_url: str = "postgresql+asyncpg://jobradar:jobradar@localhost:5432/jobradar"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    openrouter_api_key: str = ""
    default_llm_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_fallback_model: str = "openai/gpt-4o-mini"
    use_model_router: bool = True

    # Scraper API keys
    serpapi_api_key: str = ""
    theirstack_api_key: str = ""
    apify_api_key: str = ""
    scrapingbee_api_key: str = ""
    scrapling_enabled: bool = False

    # Auto-apply
    auto_apply_enabled: bool = False
    auto_apply_max_daily: int = 10
    auto_apply_interval_minutes: int = 60

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()

if settings.secret_key == "change-me-in-production" and not settings.debug:
    warnings.warn(
        "JR_SECRET_KEY is using the default value. Set a secure secret key "
        "in production via the JR_SECRET_KEY environment variable.",
        stacklevel=1,
    )
