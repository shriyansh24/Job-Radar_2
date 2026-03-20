"""Scrapling-based scraper for direct career page crawling.

Gracefully degrades if the scrapling package is not installed.
"""

from __future__ import annotations

import asyncio

import structlog

from app.config import Settings
from app.scraping.port import ScrapedJob, ScraperPort
from app.scraping.scrapers.adaptive_parser import AdaptiveCareerParser

logger = structlog.get_logger()

try:
    from scrapling import Fetcher, StealthyFetcher
    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False
    logger.info("scrapling_not_installed")


class ScraplingScraper(ScraperPort):
    """Scraper for arbitrary company career pages using Scrapling."""

    source_name = "scrapling"
    FAST_TIMEOUT = 30
    STEALTH_TIMEOUT = 60

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        """Not used directly for career pages — use scrape_career_page."""
        return []

    async def scrape_career_page(
        self, url: str, company_name: str, stealth: bool = False
    ) -> list[ScrapedJob]:
        """Scrape a specific career page URL."""
        if not SCRAPLING_AVAILABLE:
            logger.warning("scrapling.not_available", url=url)
            return []

        html = await self._fetch_page(url, stealth=stealth)
        if not html:
            return []

        parser = AdaptiveCareerParser(html, company_name, url)
        raw_listings = parser.extract()
        if not raw_listings:
            return []

        results: list[ScrapedJob] = []
        for listing in raw_listings:
            results.append(ScrapedJob(
                title=listing.get("title", ""),
                company_name=listing.get("company_name", company_name),
                source=self.source_name,
                source_url=listing.get("url", ""),
                location=listing.get("location"),
                description_raw=listing.get("description_raw", ""),
                job_type=listing.get("job_type"),
            ))

        logger.info("scrapling.scraped", url=url, company=company_name, count=len(results))
        return results

    async def health_check(self) -> bool:
        return SCRAPLING_AVAILABLE

    # ------------------------------------------------------------------
    # Fetching
    # ------------------------------------------------------------------

    async def _fetch_page(self, url: str, stealth: bool = False) -> str | None:
        if not stealth:
            html = await self._fetch_fast(url)
            if html:
                return html
            logger.info("scrapling.fast_failed_escalating", url=url)

        return await self._fetch_stealth(url)

    async def _fetch_fast(self, url: str) -> str | None:
        if not SCRAPLING_AVAILABLE:
            return None
        loop = asyncio.get_running_loop()
        try:
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: Fetcher().get(url, impersonate="chrome"),
                ),
                timeout=self.FAST_TIMEOUT,
            )
            if response and response.status == 200 and response.text:
                return response.text
        except Exception as e:
            logger.debug("scrapling.fast_error", url=url, error=str(e))
        return None

    async def _fetch_stealth(self, url: str) -> str | None:
        if not SCRAPLING_AVAILABLE:
            return None
        loop = asyncio.get_running_loop()
        try:
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: StealthyFetcher().fetch(url, headless=True),
                ),
                timeout=self.STEALTH_TIMEOUT,
            )
            if response and hasattr(response, "text"):
                return response.text
        except Exception as e:
            logger.error("scrapling.stealth_failed", url=url, error=str(e))
        return None
