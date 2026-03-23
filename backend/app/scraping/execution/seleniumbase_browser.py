"""SeleniumBase UC Mode browser adapter — anti-bot bypass via undetected Chrome.

Provides Tier-3 backup browser rendering using SeleniumBase in UC
(Undetected Chromedriver) mode. SeleniumBase is synchronous, so all
driver operations are wrapped in ``asyncio.to_thread`` to avoid
blocking the event loop.

Creates and destroys a driver per render() call to avoid state leakage.
Gracefully degrades if seleniumbase is not installed.
"""

from __future__ import annotations

import asyncio
import hashlib
import time

from app.scraping.execution.browser_port import BrowserPort, BrowserResult

try:
    import seleniumbase  # noqa: F401

    SELENIUMBASE_AVAILABLE = True
except ImportError:
    SELENIUMBASE_AVAILABLE = False


def _import_driver():
    """Import and return the seleniumbase Driver class.

    Isolated into a helper so tests can mock the import without
    touching the real seleniumbase package.
    """
    from seleniumbase import Driver

    return Driver


class SeleniumBaseBrowser(BrowserPort):
    """Tier-3 browser adapter using SeleniumBase UC mode for anti-bot bypass."""

    @property
    def browser_name(self) -> str:
        return "seleniumbase"

    async def render(
        self,
        url: str,
        timeout_s: int = 60,
        fingerprint: dict | None = None,
        wait_for_selector: str | None = None,
    ) -> BrowserResult:
        if not SELENIUMBASE_AVAILABLE:
            raise RuntimeError("seleniumbase not installed")
        start = time.monotonic()

        def _sync_render() -> str:
            driver_cls = _import_driver()
            driver = driver_cls(uc=True, headless=True)
            try:
                driver.get(url)
                if wait_for_selector:
                    driver.wait_for_element(wait_for_selector, timeout=timeout_s)
                return driver.page_source
            finally:
                driver.quit()

        html = await asyncio.to_thread(_sync_render)
        duration = int((time.monotonic() - start) * 1000)
        content_hash = hashlib.sha256(html.encode()).hexdigest()[:64]
        return BrowserResult(
            html=html,
            status_code=200,
            url_final=url,
            duration_ms=duration,
            content_hash=content_hash,
        )

    async def health_check(self) -> bool:
        return SELENIUMBASE_AVAILABLE

    async def close(self) -> None:
        pass  # SeleniumBase creates/destroys driver per-render
