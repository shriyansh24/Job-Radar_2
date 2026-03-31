from __future__ import annotations

from typing import Literal
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "change-me-in-production"
DEFAULT_DATABASE_URL = "postgresql+asyncpg://jobradar:jobradar@localhost:5432/jobradar"
DEFAULT_REDIS_URL = "redis://:jobradar-redis@localhost:6379/0"


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
    database_url: str = DEFAULT_DATABASE_URL
    database_echo: bool = False

    # Redis
    redis_url: str = DEFAULT_REDIS_URL
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
    operator_emails: list[str] = []
    frontend_base_url: str = "http://localhost:5173"

    # Google / Gmail
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:8000/api/v1/settings/integrations/google/callback"
    google_gmail_sync_query: str = (
        "newer_than:30d -category:promotions -category:social -category:forums"
    )
    google_gmail_sync_max_messages: int = 25

    # Intel GPU acceleration (optional - requires openvino or ipex)
    intel_gpu_enabled: bool = False
    openvino_cache_dir: str = ""

    # API rate limits
    api_rate_limit_per_minute: int = 120
    login_rate_limit_per_minute: int = 10


def validate_runtime_settings(settings: Settings) -> None:
    normalized_origins = [origin.strip() for origin in settings.cors_origins if origin.strip()]
    normalized_operator_emails = [
        email.strip().lower() for email in settings.operator_emails if email.strip()
    ]

    if settings.secret_key == DEFAULT_SECRET_KEY and not settings.debug:
        raise RuntimeError(
            "JR_SECRET_KEY is using the default value. Set a secure secret key "
            "or enable JR_DEBUG for local-only development."
        )
    if not settings.database_url:
        raise RuntimeError("JR_DATABASE_URL must be set.")
    if settings.database_url == DEFAULT_DATABASE_URL and not settings.debug:
        raise RuntimeError(
            "JR_DATABASE_URL cannot use the built-in local default outside debug mode."
        )
    if not settings.redis_url:
        raise RuntimeError("JR_REDIS_URL must be set.")
    if settings.redis_url == DEFAULT_REDIS_URL and not settings.debug:
        raise RuntimeError(
            "JR_REDIS_URL cannot use the built-in local default outside debug mode."
        )
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
                "JR_CORS_ORIGINS contains an invalid origin: "
                f"{origin!r}. Use full http(s) origins."
            )
    if settings.cookie_samesite == "none" and not settings.cookie_secure:
        raise RuntimeError(
            "JR_COOKIE_SECURE must be enabled when JR_COOKIE_SAMESITE is set to 'none'."
        )
    if not settings.debug and not settings.cookie_secure:
        raise RuntimeError(
            "JR_COOKIE_SECURE must be enabled when JR_DEBUG is false."
        )
    if not settings.trusted_hosts:
        raise RuntimeError("JR_TRUSTED_HOSTS must include at least one host.")
    if "*" in settings.trusted_hosts and not settings.debug:
        raise RuntimeError("JR_TRUSTED_HOSTS cannot use '*' outside debug mode.")
    if not settings.debug and not normalized_operator_emails:
        raise RuntimeError(
            "JR_OPERATOR_EMAILS must include at least one operator email outside debug mode."
        )
    if settings.api_rate_limit_per_minute <= 0:
        raise RuntimeError("JR_API_RATE_LIMIT_PER_MINUTE must be greater than zero.")
    if settings.login_rate_limit_per_minute <= 0:
        raise RuntimeError("JR_LOGIN_RATE_LIMIT_PER_MINUTE must be greater than zero.")
    if settings.google_gmail_sync_max_messages <= 0:
        raise RuntimeError("JR_GOOGLE_GMAIL_SYNC_MAX_MESSAGES must be greater than zero.")


settings = Settings()
