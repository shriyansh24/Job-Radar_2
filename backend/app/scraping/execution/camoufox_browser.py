"""Camoufox browser adapter — anti-detect Firefox via Playwright.

Provides Tier-3 browser rendering using Camoufox, a fingerprint-resistant
Firefox fork built on Playwright. Creates a fresh browser context per
render() call via async context manager to avoid state leakage.

Gracefully degrades if camoufox is not installed.
"""

from __future__ import annotations

import hashlib
import time

from app.scraping.execution.browser_port import BrowserPort, BrowserResult

try:
    from camoufox.async_api import AsyncCamoufox

    CAMOUFOX_AVAILABLE = True
except ImportError:
    AsyncCamoufox = None  # type: ignore[assignment,misc]
    CAMOUFOX_AVAILABLE = False


class CamoufoxBrowser(BrowserPort):
    """Tier-3 browser adapter using Camoufox for anti-detect browsing."""

    @property
    def browser_name(self) -> str:
        return "camoufox"

    async def render(
        self,
        url: str,
        timeout_s: int = 60,
        fingerprint: dict | None = None,
        wait_for_selector: str | None = None,
    ) -> BrowserResult:
        if not CAMOUFOX_AVAILABLE:
            raise RuntimeError("camoufox not installed")
        config = fingerprint or {}
        start = time.monotonic()
        async with AsyncCamoufox(config=config, headless=True) as browser:
            page = await browser.new_page()
            await page.goto(url, timeout=timeout_s * 1000)
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=timeout_s * 1000)
            html = await page.content()
            url_final = page.url
        duration = int((time.monotonic() - start) * 1000)
        content_hash = hashlib.sha256(html.encode()).hexdigest()[:64]
        return BrowserResult(
            html=html,
            status_code=200,
            url_final=url_final,
            duration_ms=duration,
            content_hash=content_hash,
        )

    async def health_check(self) -> bool:
        return CAMOUFOX_AVAILABLE

    async def close(self) -> None:
        pass  # Camoufox uses context manager per-render, no persistent state
