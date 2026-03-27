from __future__ import annotations

from typing import Literal
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="JR_", extra="ignore")

    # App
    app_name: str = "JobRadar V2"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # Auth
    secret_key: str = DEFAULT_SECRET_KEY
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    access_cookie_name: str = "jr_access_token"
    refresh_cookie_name: str = "jr_refresh_token"
    csrf_cookie_name: str = "jr_csrf_token"
    csrf_header_name: str = "X-CSRF-Token"
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    # Database
    database_url: str = "postgresql+asyncpg://jobradar:jobradar@localhost:5432/jobradar"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://:jobradar-redis@localhost:6379/0"
    redis_use_tls: bool = False

    # LLM
    openrouter_api_key: str = ""
    default_llm_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_fallback_model: str = "openai/gpt-4o-mini"
    use_model_router: bool = True

    # Scraper API keys
    serpapi_api_key: str = ""
    theirstack_api_key: str = ""
    apify_api_key: str = ""

    # Auto-apply
    auto_apply_enabled: bool = False
    auto_apply_max_daily: int = 10
    auto_apply_interval_minutes: int = 60

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]
    cors_methods: list[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    cors_headers: list[str] = [
        "Accept",
        "Authorization",
        "Content-Type",
        "X-CSRF-Token",
        "X-Request-ID",
    ]
    trusted_hosts: list[str] = ["localhost", "127.0.0.1", "backend", "test"]

    # Intel GPU acceleration (optional - requires openvino or ipex)
    intel_gpu_enabled: bool = False
    openvino_cache_dir: str = ""

    # API rate limits
    api_rate_limit_per_minute: int = 120
    login_rate_limit_per_minute: int = 10


def validate_runtime_settings(settings: Settings) -> None:
    normalized_origins = [origin.strip() for origin in settings.cors_origins if origin.strip()]

    if settings.secret_key == DEFAULT_SECRET_KEY and not settings.debug:
        raise RuntimeError(
            "JR_SECRET_KEY is using the default value. Set a secure secret key "
            "or enable JR_DEBUG for local-only development."
        )
    if not settings.database_url:
        raise RuntimeError("JR_DATABASE_URL must be set.")
    if not settings.redis_url:
        raise RuntimeError("JR_REDIS_URL must be set.")
    parsed_redis = urlparse(settings.redis_url)
    if parsed_redis.scheme not in {"redis", "rediss"} or not parsed_redis.hostname:
        raise RuntimeError(
            "JR_REDIS_URL must use redis:// or rediss:// with an explicit host."
        )
    if not normalized_origins:
        raise RuntimeError("JR_CORS_ORIGINS must include at least one explicit origin.")
    if "*" in normalized_origins:
        raise RuntimeError(
            "JR_CORS_ORIGINS cannot include '*' when credentialed cookie auth is enabled."
        )
    for origin in normalized_origins:
        parsed = urlparse(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise RuntimeError(
                f"JR_CORS_ORIGINS contains an invalid origin: {origin!r}. Use full http(s) origins."
            )
    if settings.cookie_samesite == "none" and not settings.cookie_secure:
        raise RuntimeError(
            "JR_COOKIE_SECURE must be enabled when JR_COOKIE_SAMESITE is set to 'none'."
        )
    if not settings.trusted_hosts:
        raise RuntimeError("JR_TRUSTED_HOSTS must include at least one host.")
    if "*" in settings.trusted_hosts and not settings.debug:
        raise RuntimeError("JR_TRUSTED_HOSTS cannot use '*' outside debug mode.")
    if settings.api_rate_limit_per_minute <= 0:
        raise RuntimeError("JR_API_RATE_LIMIT_PER_MINUTE must be greater than zero.")
    if settings.login_rate_limit_per_minute <= 0:
        raise RuntimeError("JR_LOGIN_RATE_LIMIT_PER_MINUTE must be greater than zero.")


settings = Settings()
