"""Browser pool with tier-separated concurrency governance.

Controls admission: how many browser sessions can run concurrently,
separated by tier. Does NOT own browser instances -- adapters manage
their own lifecycle. This module only enforces slot limits.

Tier mapping:
  - Tier 2: lightweight browser sessions (e.g. Nodriver)
  - Tier 3: heavyweight browser sessions (e.g. Camoufox, SeleniumBase UC)
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from app.scraping.constants import MAX_PER_DOMAIN_CONCURRENCY


class BrowserPool:
    """Manages browser session concurrency and per-domain limits.

    Does NOT own browser instances (adapters manage their own).
    Controls admission: how many browser sessions can run concurrently.
    """

    def __init__(
        self,
        max_tier2: int = 8,
        max_tier3: int = 3,
        max_per_domain: int = MAX_PER_DOMAIN_CONCURRENCY,
    ):
        self._tier2_sem = asyncio.Semaphore(max_tier2)
        self._tier3_sem = asyncio.Semaphore(max_tier3)
        self._domain_sems: dict[str, asyncio.Semaphore] = {}
        self._domain_lock = asyncio.Lock()
        self._max_per_domain = max_per_domain
        self._active = 0

    async def _get_domain_sem(self, domain: str) -> asyncio.Semaphore:
        """Return (or lazily create) the per-domain semaphore."""
        async with self._domain_lock:
            if domain not in self._domain_sems:
                self._domain_sems[domain] = asyncio.Semaphore(
                    self._max_per_domain
                )
            return self._domain_sems[domain]

    @asynccontextmanager
    async def acquire(
        self, tier: int, domain: str | None = None
    ) -> AsyncIterator[None]:
        """Acquire a browser session slot.  Blocks until available.

        Args:
            tier: Execution tier (2 or 3).  Tiers >= 3 use the tier-3
                  semaphore; anything lower uses tier-2.
            domain: Optional domain name for per-domain throttling.
        """
        sem = self._tier3_sem if tier >= 3 else self._tier2_sem
        domain_sem = (
            await self._get_domain_sem(domain) if domain else None
        )

        # Acquire domain semaphore first (more specific), then tier
        if domain_sem:
            await domain_sem.acquire()
        await sem.acquire()
        self._active += 1
        try:
            yield
        finally:
            self._active -= 1
            sem.release()
            if domain_sem:
                domain_sem.release()

    @property
    def active_sessions(self) -> int:
        """Number of currently in-flight browser sessions."""
        return self._active

    async def cleanup_idle_domains(self, active_domains: set[str]) -> None:
        """Remove semaphores for domains no longer being scraped.

        Should be called periodically to avoid unbounded growth of
        ``_domain_sems``.
        """
        async with self._domain_lock:
            stale = set(self._domain_sems) - active_domains
            for d in stale:
                del self._domain_sems[d]
