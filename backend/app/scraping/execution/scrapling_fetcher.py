"""Scrapling dual-mode adapter — fast HTTP + stealth browser rendering.

Implements BOTH FetcherPort (Tier 1) and BrowserPort (Tier 2):
  - fetch()  = fast mode via Fetcher (plain HTTP, no JS)
  - render() = stealth mode via StealthyFetcher (headless browser)

Gracefully degrades if scrapling is not installed.
"""
from __future__ import annotations

import asyncio
import hashlib
import time

from app.scraping.execution.browser_port import BrowserPort, BrowserResult
from app.scraping.execution.fetcher_port import FetcherPort, FetchResult

try:
    from scrapling import Fetcher, StealthyFetcher

    SCRAPLING_AVAILABLE = True
except ImportError:
    Fetcher = None  # type: ignore[assignment,misc]
    StealthyFetcher = None  # type: ignore[assignment,misc]
    SCRAPLING_AVAILABLE = False


class ScraplingFetcher(FetcherPort, BrowserPort):
    """Dual-mode scraping adapter backed by the scrapling library."""

    @property
    def fetcher_name(self) -> str:
        return "scrapling_fast"

    @property
    def browser_name(self) -> str:
        return "scrapling_stealth"

    async def fetch(
        self,
        url: str,
        timeout_s: int = 30,
        user_agent: str | None = None,
    ) -> FetchResult:
        if not SCRAPLING_AVAILABLE:
            raise RuntimeError("scrapling not installed")
        start = time.monotonic()
        fetcher = Fetcher()
        resp = await asyncio.to_thread(fetcher.get, url, timeout=timeout_s)
        duration = int((time.monotonic() - start) * 1000)
        html = resp.text if hasattr(resp, "text") else str(resp)
        content_hash = hashlib.sha256(html.encode()).hexdigest()[:64]
        return FetchResult(
            html=html,
            status_code=getattr(resp, "status_code", 200),
            headers={},
            url_final=url,
            duration_ms=duration,
            content_hash=content_hash,
        )

    async def render(
        self,
        url: str,
        timeout_s: int = 60,
        fingerprint: dict | None = None,
        wait_for_selector: str | None = None,
    ) -> BrowserResult:
        if not SCRAPLING_AVAILABLE:
            raise RuntimeError("scrapling not installed")
        start = time.monotonic()
        fetcher = StealthyFetcher()
        resp = await asyncio.to_thread(fetcher.fetch, url, headless=True)
        duration = int((time.monotonic() - start) * 1000)
        html = resp.text if hasattr(resp, "text") else str(resp)
        content_hash = hashlib.sha256(html.encode()).hexdigest()[:64]
        return BrowserResult(
            html=html,
            status_code=200,
            url_final=url,
            duration_ms=duration,
            content_hash=content_hash,
        )

    async def health_check(self) -> bool:
        return SCRAPLING_AVAILABLE

    async def close(self) -> None:
        pass
