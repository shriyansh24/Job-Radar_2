"""Nodriver browser adapter — undetected Chrome via CDP.

Provides Tier-2 browser rendering using nodriver (undetected-chromedriver
successor). Creates a fresh browser per render() call to avoid state leakage.

Gracefully degrades if nodriver is not installed.
"""
from __future__ import annotations

import hashlib
import time

from app.scraping.execution.browser_port import BrowserPort, BrowserResult

try:
    import nodriver as uc

    NODRIVER_AVAILABLE = True
except ImportError:
    uc = None  # type: ignore[assignment]
    NODRIVER_AVAILABLE = False


class NodriverBrowser(BrowserPort):
    """Tier-2 browser adapter using nodriver for stealth Chrome automation."""

    @property
    def browser_name(self) -> str:
        return "nodriver"

    async def render(
        self,
        url: str,
        timeout_s: int = 60,
        fingerprint: dict | None = None,
        wait_for_selector: str | None = None,
    ) -> BrowserResult:
        if not NODRIVER_AVAILABLE:
            raise RuntimeError("nodriver not installed")
        start = time.monotonic()
        browser = await uc.start()
        try:
            page = await browser.get(url)
            if wait_for_selector:
                await page.find(wait_for_selector, timeout=timeout_s)
            else:
                await page.sleep(2)
            html = await page.get_content()
            duration = int((time.monotonic() - start) * 1000)
            content_hash = hashlib.sha256(html.encode()).hexdigest()[:64]
            return BrowserResult(
                html=html,
                status_code=200,
                url_final=str(page.url),
                duration_ms=duration,
                content_hash=content_hash,
            )
        finally:
            browser.stop()

    async def health_check(self) -> bool:
        return NODRIVER_AVAILABLE

    async def close(self) -> None:
        pass
