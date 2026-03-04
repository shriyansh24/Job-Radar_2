from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Scraping APIs
    SERPAPI_KEY: str = ""
    THEIRSTACK_KEY: str = ""
    APIFY_KEY: str = ""
    SCRAPINGBEE_KEY: str = ""

    # LLM Enrichment via OpenRouter
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_PRIMARY_MODEL: str = "anthropic/claude-3-5-haiku"
    OPENROUTER_FALLBACK_MODEL: str = "openai/gpt-4o-mini"

    # App Config
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/jobradar.db"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 5173
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
