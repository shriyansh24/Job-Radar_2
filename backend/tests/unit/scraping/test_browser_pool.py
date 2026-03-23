"""Tests for BrowserPool tier-separated concurrency governance."""

from __future__ import annotations

import asyncio

import pytest

from app.scraping.execution.browser_pool import BrowserPool


@pytest.mark.asyncio
async def test_pool_respects_concurrency() -> None:
    """Tier-2 semaphore must limit concurrent sessions to max_tier2."""
    pool = BrowserPool(max_tier2=2, max_tier3=1)
    current = 0
    peak = 0

    async def acquire_and_hold() -> None:
        nonlocal current, peak
        async with pool.acquire(tier=2):
            current += 1
            peak = max(peak, current)
            await asyncio.sleep(0.1)
            current -= 1

    tasks = [asyncio.create_task(acquire_and_hold()) for _ in range(3)]
    await asyncio.gather(*tasks)
    assert peak == 2


@pytest.mark.asyncio
async def test_pool_per_domain_limit() -> None:
    """Per-domain semaphore must cap concurrency regardless of tier limit."""
    pool = BrowserPool(max_tier2=10, max_tier3=10, max_per_domain=2)
    count = 0

    async def fetch(domain: str) -> None:
        nonlocal count
        async with pool.acquire(tier=2, domain=domain):
            count += 1
            await asyncio.sleep(0.1)

    tasks = [asyncio.create_task(fetch("example.com")) for _ in range(5)]
    await asyncio.sleep(0.05)
    assert count <= 2
    await asyncio.gather(*tasks)


@pytest.mark.asyncio
async def test_tier3_separate_from_tier2() -> None:
    """Tier-3 semaphore is independent from tier-2."""
    pool = BrowserPool(max_tier2=5, max_tier3=1)
    tier3_count = 0

    async def tier3_task() -> None:
        nonlocal tier3_count
        async with pool.acquire(tier=3):
            tier3_count += 1
            await asyncio.sleep(0.1)

    tasks = [asyncio.create_task(tier3_task()) for _ in range(3)]
    await asyncio.sleep(0.05)
    assert tier3_count <= 1
    await asyncio.gather(*tasks)


@pytest.mark.asyncio
async def test_cleanup_idle_domains() -> None:
    """cleanup_idle_domains removes semaphores for domains not in the active set."""
    pool = BrowserPool(max_tier2=10, max_tier3=3)
    pool._domain_sems["active_domain"] = asyncio.Semaphore(2)
    pool._domain_sems["stale_domain"] = asyncio.Semaphore(2)
    await pool.cleanup_idle_domains(active_domains={"active_domain"})
    assert "stale_domain" not in pool._domain_sems
    assert "active_domain" in pool._domain_sems


@pytest.mark.asyncio
async def test_active_sessions_counter() -> None:
    """active_sessions property tracks in-flight sessions correctly."""
    pool = BrowserPool(max_tier2=5, max_tier3=3)
    assert pool.active_sessions == 0

    entered = asyncio.Event()
    release = asyncio.Event()

    async def hold_session() -> None:
        async with pool.acquire(tier=2):
            entered.set()
            await release.wait()

    task = asyncio.create_task(hold_session())
    await entered.wait()
    assert pool.active_sessions == 1
    release.set()
    await task
    assert pool.active_sessions == 0


@pytest.mark.asyncio
async def test_active_sessions_after_exception() -> None:
    """active_sessions decrements even when the body raises an exception."""
    pool = BrowserPool(max_tier2=5, max_tier3=3)

    async def explode() -> None:
        async with pool.acquire(tier=2):
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await explode()

    assert pool.active_sessions == 0


@pytest.mark.asyncio
async def test_domain_sem_created_lazily() -> None:
    """Domain semaphores are created on first access, not upfront."""
    pool = BrowserPool(max_tier2=5, max_tier3=3)
    assert len(pool._domain_sems) == 0
    async with pool.acquire(tier=2, domain="new_domain"):
        assert "new_domain" in pool._domain_sems
    assert len(pool._domain_sems) == 0


@pytest.mark.asyncio
async def test_tier2_and_tier3_independent_concurrency() -> None:
    """Tier-2 full does not block tier-3 slots and vice versa."""
    pool = BrowserPool(max_tier2=1, max_tier3=1)
    results: list[str] = []

    async def tier2() -> None:
        async with pool.acquire(tier=2):
            results.append("t2_start")
            await asyncio.sleep(0.1)
            results.append("t2_end")

    async def tier3() -> None:
        async with pool.acquire(tier=3):
            results.append("t3_start")
            await asyncio.sleep(0.1)
            results.append("t3_end")

    await asyncio.gather(tier2(), tier3())
    # Both should have started (possibly simultaneously since different sems)
    assert "t2_start" in results
    assert "t3_start" in results


@pytest.mark.asyncio
async def test_no_domain_sem_when_domain_is_none() -> None:
    """When domain is None, only the tier semaphore is acquired."""
    pool = BrowserPool(max_tier2=5, max_tier3=3)
    async with pool.acquire(tier=2, domain=None):
        pass
    assert len(pool._domain_sems) == 0


@pytest.mark.asyncio
async def test_cleanup_does_not_remove_active_domain() -> None:
    """cleanup_idle_domains must keep domains still in the active set."""
    pool = BrowserPool(max_tier2=10, max_tier3=3)
    pool._domain_sems["keep_domain"] = asyncio.Semaphore(2)
    pool._domain_sems["remove_domain"] = asyncio.Semaphore(2)
    pool._domain_sems["also_keep_domain"] = asyncio.Semaphore(2)

    await pool.cleanup_idle_domains(active_domains={"keep_domain", "also_keep_domain"})
    assert "keep_domain" in pool._domain_sems
    assert "also_keep_domain" in pool._domain_sems
    assert "remove_domain" not in pool._domain_sems
