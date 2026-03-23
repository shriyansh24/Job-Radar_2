"""Tests for ScrapingService.run_target_batch() — target-based pipeline integration."""

from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _mock_service():
    """Create a ScrapingService with mocked DB (bypass __init__)."""
    from app.scraping.service import ScrapingService

    svc = ScrapingService.__new__(ScrapingService)
    svc.db = MagicMock()
    svc.db.add = MagicMock()
    svc.db.commit = AsyncMock()
    svc.db.rollback = AsyncMock()
    return svc


def _target(**kw):
    """Create a fake ScrapeTarget SimpleNamespace."""
    defaults = dict(
        id="t1",
        url="https://boards.greenhouse.io/test",
        company_name="Test Corp",
        ats_vendor="greenhouse",
        ats_board_token="test",
        start_tier=0,
        max_tier=3,
        last_success_tier=None,
        consecutive_failures=0,
        content_hash=None,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def _registry_for_ats(jobs_result=None):
    """Build a mock AdapterRegistry that returns an ATS binding."""
    if jobs_result is None:
        jobs_result = []
    registry = MagicMock()
    binding = MagicMock(method="fetch_jobs", is_browser=False)
    registry.get.return_value = binding
    fetch_jobs_fn = AsyncMock(return_value=jobs_result)
    registry.resolve.return_value = (MagicMock(), fetch_jobs_fn)
    return registry


def _registry_for_fetcher(fetch_result=None):
    """Build a mock AdapterRegistry that returns a fetcher binding."""
    if fetch_result is None:
        fetch_result = SimpleNamespace(
            status_code=200,
            html="<html><body>jobs</body></html>",
            content_hash="abc123",
            duration_ms=150,
        )
    registry = MagicMock()
    binding = MagicMock(method="fetch", is_browser=False)
    registry.get.return_value = binding
    fetch_fn = AsyncMock(return_value=fetch_result)
    registry.resolve.return_value = (MagicMock(), fetch_fn)
    return registry


def _registry_for_browser(render_result=None):
    """Build a mock AdapterRegistry that returns a browser binding."""
    if render_result is None:
        render_result = SimpleNamespace(
            status_code=200,
            html="<html><body>rendered jobs</body></html>",
            content_hash="def456",
            duration_ms=3000,
        )
    registry = MagicMock()
    binding = MagicMock(method="render", is_browser=True)
    registry.get.return_value = binding
    render_fn = AsyncMock(return_value=render_result)
    registry.resolve.return_value = (MagicMock(), render_fn)
    return registry


# ── Core behaviour ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_target_batch_returns_result_keys():
    """Result dict must contain all expected keys."""
    svc = _mock_service()
    registry = _registry_for_ats()
    pool = MagicMock()

    results = await svc.run_target_batch(
        targets=[_target()],
        run_id="run1",
        adapter_registry=registry,
        browser_pool=pool,
    )
    assert "jobs_found" in results
    assert "targets_attempted" in results
    assert "targets_succeeded" in results
    assert "targets_failed" in results
    assert "errors" in results


@pytest.mark.asyncio
async def test_run_target_batch_empty_targets():
    """Empty target list should produce zero counts and commit."""
    svc = _mock_service()
    registry = MagicMock()
    pool = MagicMock()

    results = await svc.run_target_batch(
        targets=[],
        run_id="run1",
        adapter_registry=registry,
        browser_pool=pool,
    )
    assert results["targets_attempted"] == 0
    assert results["jobs_found"] == 0
    assert results["targets_succeeded"] == 0
    assert results["targets_failed"] == 0
    svc.db.commit.assert_awaited_once()


# ── ATS (tier 0) path ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ats_target_success_counts_jobs():
    """ATS adapter returning jobs should count them."""
    svc = _mock_service()
    fake_jobs = [{"title": "SWE"}, {"title": "PM"}]
    registry = _registry_for_ats(jobs_result=fake_jobs)
    pool = MagicMock()

    results = await svc.run_target_batch(
        targets=[_target()],
        run_id="run1",
        adapter_registry=registry,
        browser_pool=pool,
    )
    assert results["jobs_found"] == 2
    assert results["targets_succeeded"] == 1
    assert results["targets_failed"] == 0


@pytest.mark.asyncio
async def test_ats_target_empty_jobs_still_succeeds():
    """ATS returning empty list is still a success (0 jobs)."""
    svc = _mock_service()
    registry = _registry_for_ats(jobs_result=[])
    pool = MagicMock()

    results = await svc.run_target_batch(
        targets=[_target()],
        run_id="run1",
        adapter_registry=registry,
        browser_pool=pool,
    )
    assert results["jobs_found"] == 0
    assert results["targets_succeeded"] == 1


# ── Fetcher (tier 1) path ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetcher_success_no_escalation():
    """Fetcher returning 200 with content should succeed without escalation."""
    svc = _mock_service()
    target = _target(ats_vendor="unknown_ats", start_tier=1)
    registry = _registry_for_fetcher()
    pool = MagicMock()

    with patch("app.scraping.execution.escalation_engine.should_escalate", return_value=None):
        results = await svc.run_target_batch(
            targets=[target],
            run_id="run1",
            adapter_registry=registry,
            browser_pool=pool,
        )
    assert results["targets_succeeded"] == 1
    assert results["targets_failed"] == 0


@pytest.mark.asyncio
async def test_fetcher_escalation_exhausts_all_tiers():
    """When should_escalate always triggers, all steps are tried then target fails."""
    from app.scraping.execution.escalation_engine import EscalationDecision, EscalationReason

    svc = _mock_service()
    target = _target(ats_vendor="unknown_ats", start_tier=1, max_tier=1)
    registry = _registry_for_fetcher()
    pool = MagicMock()

    decision = EscalationDecision(reason=EscalationReason.EMPTY_RESPONSE)
    with patch("app.scraping.execution.escalation_engine.should_escalate", return_value=decision):
        results = await svc.run_target_batch(
            targets=[target],
            run_id="run1",
            adapter_registry=registry,
            browser_pool=pool,
        )
    assert results["targets_failed"] == 1
    assert len(results["errors"]) == 1


# ── Browser path ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_browser_target_acquires_pool():
    """Browser-based step should acquire from browser_pool context manager."""
    svc = _mock_service()
    target = _target(ats_vendor="unknown_ats", start_tier=2, max_tier=2)

    render_result = SimpleNamespace(
        status_code=200,
        html="<html>rendered</html>",
        content_hash="h1",
        duration_ms=2000,
    )
    registry = _registry_for_browser(render_result)

    pool_cm = MagicMock()
    pool_cm.__aenter__ = AsyncMock(return_value=None)
    pool_cm.__aexit__ = AsyncMock(return_value=False)
    pool = MagicMock()
    pool.acquire.return_value = pool_cm

    with patch("app.scraping.execution.escalation_engine.should_escalate", return_value=None):
        results = await svc.run_target_batch(
            targets=[target],
            run_id="run1",
            adapter_registry=registry,
            browser_pool=pool,
        )
    pool.acquire.assert_called_once()
    assert results["targets_succeeded"] == 1


# ── Error handling ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_exception_in_adapter_records_failure():
    """An exception from the adapter method should be caught and recorded."""
    svc = _mock_service()
    registry = MagicMock()
    binding = MagicMock(method="fetch", is_browser=False)
    registry.get.return_value = binding
    registry.resolve.return_value = (
        MagicMock(),
        AsyncMock(side_effect=ConnectionError("refused")),
    )

    target = _target(ats_vendor="unknown_ats", start_tier=1, max_tier=1)
    pool = MagicMock()

    results = await svc.run_target_batch(
        targets=[target],
        run_id="run1",
        adapter_registry=registry,
        browser_pool=pool,
    )
    assert results["targets_failed"] == 1
    # ScrapeAttempt was added to DB
    svc.db.add.assert_called()


@pytest.mark.asyncio
async def test_timeout_records_escalation():
    """asyncio.TimeoutError should record an escalated attempt."""
    svc = _mock_service()
    registry = MagicMock()
    binding = MagicMock(method="fetch", is_browser=False)
    registry.get.return_value = binding
    registry.resolve.return_value = (MagicMock(), AsyncMock(side_effect=asyncio.TimeoutError()))

    target = _target(ats_vendor="unknown_ats", start_tier=1, max_tier=1)
    pool = MagicMock()

    results = await svc.run_target_batch(
        targets=[target],
        run_id="run1",
        adapter_registry=registry,
        browser_pool=pool,
    )
    assert results["targets_failed"] == 1


# ── Multiple targets ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_multiple_targets_processed():
    """Multiple targets should all be processed concurrently."""
    svc = _mock_service()
    targets = [_target(id=f"t{i}", company_name=f"Corp {i}") for i in range(3)]
    registry = _registry_for_ats(jobs_result=[{"title": "job"}])
    pool = MagicMock()

    results = await svc.run_target_batch(
        targets=targets,
        run_id="run1",
        adapter_registry=registry,
        browser_pool=pool,
    )
    assert results["targets_attempted"] == 3
    assert results["targets_succeeded"] == 3
    assert results["jobs_found"] == 3


# ── DB commit / rollback ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_db_commit_called_after_processing():
    """DB commit is called once after all targets are processed."""
    svc = _mock_service()
    registry = _registry_for_ats()
    pool = MagicMock()

    await svc.run_target_batch(
        targets=[_target()],
        run_id="run1",
        adapter_registry=registry,
        browser_pool=pool,
    )
    svc.db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_db_rollback_on_commit_failure():
    """If commit raises, rollback should be called."""
    svc = _mock_service()
    svc.db.commit = AsyncMock(side_effect=Exception("db error"))
    registry = _registry_for_ats()
    pool = MagicMock()

    results = await svc.run_target_batch(
        targets=[_target()],
        run_id="run1",
        adapter_registry=registry,
        browser_pool=pool,
    )
    svc.db.rollback.assert_awaited_once()
    # Should still return results, not raise
    assert results["targets_attempted"] == 1


@pytest.mark.asyncio
async def test_batch_rolls_back_when_target_task_raises():
    """An uncaught target task exception should abort the batch and roll back."""
    from app.scraping.control.tier_router import ExecutionPlan, Step

    svc = _mock_service()
    good_id = uuid.uuid4()
    bad_id = uuid.uuid4()
    good_target = _target(id=good_id, ats_vendor="greenhouse", ats_board_token="test")
    bad_target = _target(id=bad_id, ats_vendor="greenhouse", ats_board_token="broken")
    registry = _registry_for_ats(jobs_result=[{"title": "job"}])
    pool = MagicMock()

    good_plan = ExecutionPlan(
        primary_tier=0,
        max_tier=0,
        primary_step=Step(tier=0, scraper_name="greenhouse", parser_name="greenhouse_api"),
        fallback_chain=(),
        rate_policy="greenhouse",
    )

    def route(target):
        if target.id == bad_id:
            raise RuntimeError("route failed")
        return good_plan

    with patch("app.scraping.control.tier_router.TierRouter.route", side_effect=route):
        results = await svc.run_target_batch(
            targets=[good_target, bad_target],
            run_id="run1",
            adapter_registry=registry,
            browser_pool=pool,
        )

    svc.db.rollback.assert_awaited_once()
    svc.db.commit.assert_not_awaited()
    assert results["targets_failed"] == 1
    assert any("route failed" in error for error in results["errors"])


@pytest.mark.asyncio
async def test_pagination_timeout_aborts_crawl_without_hanging():
    """Pagination should be bounded by the service timeout."""
    from app.scraping.control.tier_router import ExecutionPlan, Step

    svc = _mock_service()
    target = _target(
        id=uuid.uuid4(),
        url="https://example.com/jobs",
        company_name="Example",
        ats_vendor=None,
        source_kind="career_page",
        start_tier=1,
        max_tier=1,
    )
    registry = _registry_for_fetcher()
    pool = MagicMock()

    async def slow_crawl(*args, **kwargs):
        await asyncio.sleep(0.05)
        return None

    plan = ExecutionPlan(
        primary_tier=1,
        max_tier=1,
        primary_step=Step(tier=1, scraper_name="cloudscraper", timeout_s=1),
        fallback_chain=(),
        rate_policy="generic",
    )

    with (
        patch("app.scraping.control.tier_router.TierRouter.route", return_value=plan),
        patch("app.scraping.execution.escalation_engine.should_escalate", return_value=None),
        patch("app.scraping.execution.page_crawler.PageCrawler.crawl", side_effect=slow_crawl),
    ):
        svc.PAGINATION_TIMEOUT_S = 0.01
        results = await svc.run_target_batch(
            targets=[target],
            run_id="run1",
            adapter_registry=registry,
            browser_pool=pool,
        )

    svc.db.commit.assert_awaited_once()
    assert results["targets_succeeded"] == 1
    assert results["targets_failed"] == 0
