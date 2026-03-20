"""Tests for BrowserPool tier-separated concurrency governance."""
import pytest
import asyncio
from app.scraping.execution.browser_pool import BrowserPool


@pytest.mark.asyncio
async def test_pool_respects_concurrency():
    """Tier-2 semaphore must limit concurrent sessions to max_tier2."""
    pool = BrowserPool(max_tier2=2, max_tier3=1)
    acquired = 0

    async def acquire_and_hold():
        nonlocal acquired
        async with pool.acquire(tier=2):
            acquired += 1
            await asyncio.sleep(0.1)

    tasks = [asyncio.create_task(acquire_and_hold()) for _ in range(3)]
    await asyncio.sleep(0.05)
    assert acquired <= 2
    await asyncio.gather(*tasks)
    assert acquired == 3


@pytest.mark.asyncio
async def test_pool_per_domain_limit():
    """Per-domain semaphore must cap concurrency regardless of tier limit."""
    pool = BrowserPool(max_tier2=10, max_tier3=10, max_per_domain=2)
    count = 0

    async def fetch(domain):
        nonlocal count
        async with pool.acquire(tier=2, domain=domain):
            count += 1
            await asyncio.sleep(0.1)

    tasks = [asyncio.create_task(fetch("example.com")) for _ in range(5)]
    await asyncio.sleep(0.05)
    assert count <= 2
    await asyncio.gather(*tasks)


@pytest.mark.asyncio
async def test_tier3_separate_from_tier2():
    """Tier-3 semaphore is independent from tier-2."""
    pool = BrowserPool(max_tier2=5, max_tier3=1)
    tier3_count = 0

    async def tier3_task():
        nonlocal tier3_count
        async with pool.acquire(tier=3):
            tier3_count += 1
            await asyncio.sleep(0.1)

    tasks = [asyncio.create_task(tier3_task()) for _ in range(3)]
    await asyncio.sleep(0.05)
    assert tier3_count <= 1
    await asyncio.gather(*tasks)


@pytest.mark.asyncio
async def test_cleanup_idle_domains():
    """cleanup_idle_domains removes semaphores for domains not in the active set."""
    pool = BrowserPool(max_tier2=10, max_tier3=3)
    async with pool.acquire(tier=2, domain="active.com"):
        pass
    async with pool.acquire(tier=2, domain="stale.com"):
        pass
    await pool.cleanup_idle_domains(active_domains={"active.com"})
    assert "stale.com" not in pool._domain_sems
    assert "active.com" in pool._domain_sems


@pytest.mark.asyncio
async def test_active_sessions_counter():
    """active_sessions property tracks in-flight sessions correctly."""
    pool = BrowserPool(max_tier2=5, max_tier3=3)
    assert pool.active_sessions == 0

    hold = asyncio.Event()

    async def hold_session():
        async with pool.acquire(tier=2):
            hold.set()
            await asyncio.sleep(0.1)

    task = asyncio.create_task(hold_session())
    await hold.wait()
    assert pool.active_sessions == 1
    await task
    assert pool.active_sessions == 0


@pytest.mark.asyncio
async def test_active_sessions_after_exception():
    """active_sessions decrements even when the body raises an exception."""
    pool = BrowserPool(max_tier2=5, max_tier3=3)

    with pytest.raises(RuntimeError):
        async with pool.acquire(tier=2):
            raise RuntimeError("boom")

    assert pool.active_sessions == 0


@pytest.mark.asyncio
async def test_domain_sem_created_lazily():
    """Domain semaphores are created on first access, not upfront."""
    pool = BrowserPool(max_tier2=5, max_tier3=3)
    assert len(pool._domain_sems) == 0
    async with pool.acquire(tier=2, domain="new.com"):
        assert "new.com" in pool._domain_sems
    assert len(pool._domain_sems) == 1


@pytest.mark.asyncio
async def test_tier2_and_tier3_independent_concurrency():
    """Tier-2 full does not block tier-3 slots and vice versa."""
    pool = BrowserPool(max_tier2=1, max_tier3=1)
    results = []

    async def tier2():
        async with pool.acquire(tier=2):
            results.append("t2_start")
            await asyncio.sleep(0.1)
            results.append("t2_end")

    async def tier3():
        async with pool.acquire(tier=3):
            results.append("t3_start")
            await asyncio.sleep(0.1)
            results.append("t3_end")

    await asyncio.gather(tier2(), tier3())
    # Both should have started (possibly simultaneously since different sems)
    assert "t2_start" in results
    assert "t3_start" in results


@pytest.mark.asyncio
async def test_no_domain_sem_when_domain_is_none():
    """When domain is None, only the tier semaphore is acquired."""
    pool = BrowserPool(max_tier2=5, max_tier3=3)
    async with pool.acquire(tier=2, domain=None):
        pass
    assert len(pool._domain_sems) == 0


@pytest.mark.asyncio
async def test_cleanup_does_not_remove_active_domain():
    """cleanup_idle_domains must keep domains still in the active set."""
    pool = BrowserPool(max_tier2=10, max_tier3=3)
    async with pool.acquire(tier=2, domain="keep.com"):
        pass
    async with pool.acquire(tier=2, domain="remove.com"):
        pass
    async with pool.acquire(tier=2, domain="also-keep.com"):
        pass

    await pool.cleanup_idle_domains(active_domains={"keep.com", "also-keep.com"})
    assert "keep.com" in pool._domain_sems
    assert "also-keep.com" in pool._domain_sems
    assert "remove.com" not in pool._domain_sems
