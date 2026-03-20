"""Cloudscraper fetcher adapter — bypasses Cloudflare JS challenges.

IMPORTANT: cloudscraper uses requests.Session which is NOT thread-safe.
A new scraper session is created per call to avoid concurrency issues.
"""
from __future__ import annotations

import asyncio
import hashlib
import time

import cloudscraper as cs

from app.scraping.execution.fetcher_port import FetcherPort, FetchResult


class CloudscraperFetcher(FetcherPort):
    """Tier-1 HTTP fetcher that handles Cloudflare-protected sites."""

    @property
    def fetcher_name(self) -> str:
        return "cloudscraper"

    async def fetch(
        self,
        url: str,
        timeout_s: int = 30,
        user_agent: str | None = None,
    ) -> FetchResult:
        scraper = cs.create_scraper(
            browser={"browser": "chrome", "platform": "windows"},
        )
        if user_agent:
            scraper.headers["User-Agent"] = user_agent
        start = time.monotonic()
        try:
            resp = await asyncio.to_thread(scraper.get, url, timeout=timeout_s)
            duration = int((time.monotonic() - start) * 1000)
            content_hash = hashlib.sha256(resp.text.encode()).hexdigest()[:64]
            return FetchResult(
                html=resp.text,
                status_code=resp.status_code,
                headers=dict(resp.headers),
                url_final=str(resp.url),
                duration_ms=duration,
                content_hash=content_hash,
            )
        finally:
            scraper.close()

    async def health_check(self) -> bool:
        return True

    async def close(self) -> None:
        pass
