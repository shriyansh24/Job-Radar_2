"""Nodriver browser adapter — undetected Chrome via CDP.

Provides Tier-2 browser rendering using nodriver (undetected-chromedriver
successor). Uses a persistent browser instance with lazy initialization
and an asyncio lock to avoid spawning a new Chromium process per call.

Gracefully degrades if nodriver is not installed.
"""
from __future__ import annotations

import asyncio
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
    """Tier-2 browser adapter using nodriver for stealth Chrome automation.

    Maintains a single persistent browser instance across render() calls.
    The browser is lazily initialized on first use and protected by an
    asyncio lock to prevent concurrent startup races.
    """

    def __init__(self) -> None:
        self._browser = None
        self._lock = asyncio.Lock()

    async def _get_browser(self):
        """Lazy-init a reusable browser instance, protected by lock."""
        async with self._lock:
            if self._browser is None:
                self._browser = await uc.start()
            return self._browser

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
        browser = await self._get_browser()
        page = await browser.get(url)
        if wait_for_selector:
            await page.find(wait_for_selector, timeout=timeout_s)
        else:
            await page.sleep(2)  # wait for JS rendering
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
        # Do NOT stop browser — reuse across calls

    async def health_check(self) -> bool:
        return NODRIVER_AVAILABLE

    async def close(self) -> None:
        """Shut down the persistent browser instance."""
        if self._browser:
            self._browser.stop()
            self._browser = None
