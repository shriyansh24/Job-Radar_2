from .career_pages import career_pages_router
from .dedup import dedup_router
from .manual import manual_scraper_router
from .targets import target_scraper_router

__all__ = [
    "career_pages_router",
    "dedup_router",
    "manual_scraper_router",
    "target_scraper_router",
]
