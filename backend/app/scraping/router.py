from __future__ import annotations

from fastapi import APIRouter

from app.scraping.routes import (
    career_pages_router,
    dedup_router,
    manual_scraper_router,
    target_scraper_router,
)

router = APIRouter(prefix="/scraper", tags=["scraper"])
router.include_router(manual_scraper_router)
router.include_router(career_pages_router)
router.include_router(target_scraper_router)
router.include_router(dedup_router)
