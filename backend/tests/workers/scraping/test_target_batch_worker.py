"""Tests for ScrapingService.run_target_batch()."""

from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scraping.port import ScrapedJob


def _mock_service():
    from app.scraping.service import ScrapingService

    svc = ScrapingService.__new__(ScrapingService)
    svc.db = MagicMock()
    svc.db.add = MagicMock()
    svc.db.commit = AsyncMock()
    svc.db.rollback = AsyncMock()
    svc.settings = SimpleNamespace(app_name="JobRadar V2")
    return svc


def _target(**kw):
    defaults = dict(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        url="https://example.com/jobs",
        company_name="Test Corp",
        ats_vendor="greenhouse",
        ats_board_token="test",
        source_kind="ats_board",
        start_tier=0,
        max_tier=3,
        last_success_tier=None,
        consecutive_failures=0,
        failure_count=0,
        content_hash=None,
        etag=None,
        last_modified=None,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def _registry_for_ats(jobs_result=None):
    registry = MagicMock()
    binding = MagicMock(method="fetch_jobs", is_browser=False)
    registry.get.return_value = binding
    fetch_jobs_fn = AsyncMock(return_value=jobs_result or [])
    registry.resolve.return_value = (MagicMock(), fetch_jobs_fn)
    return registry


def _registry_for_fetcher(fetch_result=None):
    registry = MagicMock()
    binding = MagicMock(method="fetch", is_browser=False)
    registry.get.return_value = binding
    fetch_fn = AsyncMock(
        return_value=fetch_result
        or SimpleNamespace(
            status_code=200,
            html="<html><body>jobs</body></html>",
            headers={},
            content_hash="abc123",
            duration_ms=150,
        )
    )
    registry.resolve.return_value = (MagicMock(), fetch_fn)
    return registry, fetch_fn


def _registry_for_browser(render_result=None):
    registry = MagicMock()
    binding = MagicMock(method="render", is_browser=True)
    registry.get.return_value = binding
    render_fn = AsyncMock(
        return_value=render_result
        or SimpleNamespace(
            status_code=200,
            html="<html><body>rendered jobs</body></html>",
            content_hash="def456",
            duration_ms=3000,
        )
    )
    registry.resolve.return_value = (MagicMock(), render_fn)
    return registry


def _robots_allowed():
    return AsyncMock(
        return_value=SimpleNamespace(
            allowed=True,
            reason="robots_allowed",
            robots_url="https://example.com/robots.txt",
            from_cache=False,
        )
    )


def _pagination_result(*jobs):
    return SimpleNamespace(
        jobs=list(jobs),
        pages_crawled=1,
        stopped_reason="no_more_pages",
    )


@pytest.mark.asyncio
async def test_run_target_batch_returns_result_keys():
    svc = _mock_service()
    registry = _registry_for_ats()
    pool = MagicMock()

    results = await svc.run_target_batch(
        targets=[_target()],
        run_id=uuid.uuid4(),
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
    svc = _mock_service()
    registry = MagicMock()
    pool = MagicMock()

    results = await svc.run_target_batch(
        targets=[],
        run_id=uuid.uuid4(),
        adapter_registry=registry,
        browser_pool=pool,
    )

    assert results["targets_attempted"] == 0
    assert results["jobs_found"] == 0
    assert results["targets_succeeded"] == 0
    assert results["targets_failed"] == 0
    svc.db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_ats_target_success_counts_and_persists_jobs():
    svc = _mock_service()
    fake_jobs = [
        ScrapedJob(
            title="SWE",
            company_name="Test Corp",
            source="greenhouse",
            source_url="https://example.com/jobs/swe",
        ),
        ScrapedJob(
            title="PM",
            company_name="Test Corp",
            source="greenhouse",
            source_url="https://example.com/jobs/pm",
        ),
    ]
    registry = _registry_for_ats(jobs_result=fake_jobs)
    pool = MagicMock()

    with patch(
        "app.scraping.service.persist_jobs",
        AsyncMock(return_value=(2, 0)),
    ) as persist_jobs:
        results = await svc.run_target_batch(
            targets=[_target()],
            run_id=uuid.uuid4(),
            adapter_registry=registry,
            browser_pool=pool,
        )

    assert results["jobs_found"] == 2
    assert results["targets_succeeded"] == 1
    persist_jobs.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetcher_success_parses_paginated_jobs_and_persists():
    svc = _mock_service()
    target = _target(ats_vendor=None, source_kind="career_page", start_tier=1, max_tier=1)
    registry, _fetch_fn = _registry_for_fetcher(
        fetch_result=SimpleNamespace(
            status_code=200,
            html="""
                <section class="job-listings">
                  <div class="job-card">
                    <h2><a href="/jobs/frontend-engineer">Frontend Engineer</a></h2>
                    <p class="location">Austin, TX</p>
                  </div>
                </section>
            """,
            headers={},
            content_hash="abc123",
            duration_ms=150,
        )
    )
    pool = MagicMock()

    with (
        patch("app.scraping.service.evaluate_robots", _robots_allowed()),
        patch(
            "app.scraping.execution.page_crawler.PageCrawler.crawl",
            AsyncMock(
                return_value=_pagination_result(
                    {"title": "Role One", "url": "/jobs/role-one"},
                    {"title": "Role Two", "url": "/jobs/role-two"},
                )
            ),
        ),
        patch("app.scraping.service.persist_jobs", AsyncMock(return_value=(2, 0))) as persist_jobs,
    ):
        results = await svc.run_target_batch(
            targets=[target],
            run_id=uuid.uuid4(),
            adapter_registry=registry,
            browser_pool=pool,
        )

    assert results["targets_succeeded"] == 1
    assert results["jobs_found"] == 2
    persist_jobs.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetcher_zero_extraction_exhausts_target():
    from app.scraping.execution.escalation_engine import EscalationDecision, EscalationReason

    svc = _mock_service()
    target = _target(ats_vendor=None, source_kind="career_page", start_tier=1, max_tier=1)
    registry, _fetch_fn = _registry_for_fetcher(
        fetch_result=SimpleNamespace(
            status_code=200,
            html="""
                <section class="job-listings">
                  <div class="job-card">
                    <h2><a href="/jobs/frontend-engineer">Frontend Engineer</a></h2>
                    <p class="location">Austin, TX</p>
                  </div>
                </section>
            """,
            headers={},
            content_hash="abc123",
            duration_ms=150,
        )
    )
    pool = MagicMock()
    decision = EscalationDecision(reason=EscalationReason.ZERO_EXTRACTION)

    with (
        patch("app.scraping.service.evaluate_robots", _robots_allowed()),
        patch(
            "app.scraping.execution.page_crawler.PageCrawler.crawl",
            AsyncMock(return_value=_pagination_result()),
        ),
        patch("app.scraping.execution.escalation_engine.should_escalate", return_value=decision),
    ):
        results = await svc.run_target_batch(
            targets=[target],
            run_id=uuid.uuid4(),
            adapter_registry=registry,
            browser_pool=pool,
        )

    assert results["targets_failed"] == 1
    assert results["errors"] == ["Test Corp: all tiers exhausted"]


@pytest.mark.asyncio
async def test_browser_target_acquires_pool_and_persists():
    svc = _mock_service()
    target = _target(ats_vendor=None, source_kind="career_page", start_tier=2, max_tier=2)
    registry = _registry_for_browser()

    pool_cm = MagicMock()
    pool_cm.__aenter__ = AsyncMock(return_value=None)
    pool_cm.__aexit__ = AsyncMock(return_value=False)
    pool = MagicMock()
    pool.acquire.return_value = pool_cm

    with (
        patch("app.scraping.service.evaluate_robots", _robots_allowed()),
        patch(
            "app.scraping.execution.page_crawler.PageCrawler.crawl",
            AsyncMock(
                return_value=_pagination_result(
                    {"title": "Rendered role", "url": "/jobs/1"}
                )
            ),
        ),
        patch("app.scraping.service.persist_jobs", AsyncMock(return_value=(1, 0))),
    ):
        results = await svc.run_target_batch(
            targets=[target],
            run_id=uuid.uuid4(),
            adapter_registry=registry,
            browser_pool=pool,
        )

    pool.acquire.assert_called_once()
    assert results["targets_succeeded"] == 1


@pytest.mark.asyncio
async def test_conditional_headers_are_sent_to_fetchers():
    svc = _mock_service()
    target = _target(
        ats_vendor=None,
        source_kind="career_page",
        start_tier=1,
        max_tier=1,
        etag='"abc"',
        last_modified="Mon, 01 Jan 2026 00:00:00 GMT",
    )
    registry, fetch_fn = _registry_for_fetcher(
        fetch_result=SimpleNamespace(
            status_code=304,
            html="",
            headers={"ETag": '"abc"'},
            content_hash="abc123",
            duration_ms=20,
        )
    )
    pool = MagicMock()

    with patch("app.scraping.service.evaluate_robots", _robots_allowed()):
        results = await svc.run_target_batch(
            targets=[target],
            run_id=uuid.uuid4(),
            adapter_registry=registry,
            browser_pool=pool,
        )

    assert results["targets_succeeded"] == 1
    call_kwargs = fetch_fn.await_args.kwargs
    assert call_kwargs["headers"] == {
        "If-None-Match": '"abc"',
        "If-Modified-Since": "Mon, 01 Jan 2026 00:00:00 GMT",
    }


@pytest.mark.asyncio
async def test_robots_denial_blocks_target_before_fetch():
    svc = _mock_service()
    target = _target(ats_vendor=None, source_kind="career_page", start_tier=1, max_tier=1)
    registry, fetch_fn = _registry_for_fetcher()
    pool = MagicMock()

    with patch(
        "app.scraping.service.evaluate_robots",
        AsyncMock(
            return_value=SimpleNamespace(
                allowed=False,
                reason="robots_disallowed",
                robots_url="https://example.com/robots.txt",
                from_cache=False,
            )
        ),
    ):
        results = await svc.run_target_batch(
            targets=[target],
            run_id=uuid.uuid4(),
            adapter_registry=registry,
            browser_pool=pool,
        )

    assert results["targets_failed"] == 1
    assert results["errors"] == ["Test Corp: blocked by robots.txt"]
    fetch_fn.assert_not_called()


@pytest.mark.asyncio
async def test_exception_in_adapter_records_failure():
    svc = _mock_service()
    registry = MagicMock()
    binding = MagicMock(method="fetch", is_browser=False)
    registry.get.return_value = binding
    registry.resolve.return_value = (
        MagicMock(),
        AsyncMock(side_effect=ConnectionError("refused")),
    )
    target = _target(ats_vendor=None, source_kind="career_page", start_tier=1, max_tier=1)
    pool = MagicMock()

    with patch("app.scraping.service.evaluate_robots", _robots_allowed()):
        results = await svc.run_target_batch(
            targets=[target],
            run_id=uuid.uuid4(),
            adapter_registry=registry,
            browser_pool=pool,
        )

    assert results["targets_failed"] == 1
    svc.db.add.assert_called()


@pytest.mark.asyncio
async def test_timeout_records_escalation():
    svc = _mock_service()
    registry = MagicMock()
    binding = MagicMock(method="fetch", is_browser=False)
    registry.get.return_value = binding
    registry.resolve.return_value = (MagicMock(), AsyncMock(side_effect=asyncio.TimeoutError()))
    target = _target(ats_vendor=None, source_kind="career_page", start_tier=1, max_tier=1)
    pool = MagicMock()

    with patch("app.scraping.service.evaluate_robots", _robots_allowed()):
        results = await svc.run_target_batch(
            targets=[target],
            run_id=uuid.uuid4(),
            adapter_registry=registry,
            browser_pool=pool,
        )

    assert results["targets_failed"] == 1


@pytest.mark.asyncio
async def test_multiple_targets_processed():
    svc = _mock_service()
    targets = [_target(id=uuid.uuid4(), company_name=f"Corp {i}") for i in range(3)]
    registry = _registry_for_ats(
        jobs_result=[
            ScrapedJob(
                title="job",
                company_name="Corp",
                source="greenhouse",
                source_url="https://example.com/job",
            )
        ]
    )
    pool = MagicMock()

    with patch("app.scraping.service.persist_jobs", AsyncMock(return_value=(1, 0))):
        results = await svc.run_target_batch(
            targets=targets,
            run_id=uuid.uuid4(),
            adapter_registry=registry,
            browser_pool=pool,
        )

    assert results["targets_attempted"] == 3
    assert results["targets_succeeded"] == 3
    assert results["jobs_found"] == 3


@pytest.mark.asyncio
async def test_db_commit_called_after_processing():
    svc = _mock_service()
    registry = _registry_for_ats()
    pool = MagicMock()

    with patch("app.scraping.service.persist_jobs", AsyncMock(return_value=(0, 0))):
        await svc.run_target_batch(
            targets=[_target()],
            run_id=uuid.uuid4(),
            adapter_registry=registry,
            browser_pool=pool,
        )

    svc.db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_db_rollback_on_commit_failure():
    svc = _mock_service()
    svc.db.commit = AsyncMock(side_effect=Exception("db error"))
    registry = _registry_for_ats()
    pool = MagicMock()

    with patch("app.scraping.service.persist_jobs", AsyncMock(return_value=(0, 0))):
        results = await svc.run_target_batch(
            targets=[_target()],
            run_id=uuid.uuid4(),
            adapter_registry=registry,
            browser_pool=pool,
        )

    svc.db.rollback.assert_awaited_once()
    assert results["targets_attempted"] == 1


@pytest.mark.asyncio
async def test_batch_rolls_back_when_route_raises():
    from app.scraping.control.tier_router import ExecutionPlan, Step

    svc = _mock_service()
    good_id = uuid.uuid4()
    bad_id = uuid.uuid4()
    good_target = _target(id=good_id, ats_vendor="greenhouse", ats_board_token="test")
    bad_target = _target(id=bad_id, ats_vendor="greenhouse", ats_board_token="broken")
    registry = _registry_for_ats(
        jobs_result=[
            ScrapedJob(
                title="job",
                company_name="Test Corp",
                source="greenhouse",
                source_url="https://example.com/job",
            )
        ]
    )
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

    with (
        patch("app.scraping.control.tier_router.TierRouter.route", side_effect=route),
        patch("app.scraping.service.persist_jobs", AsyncMock(return_value=(1, 0))),
    ):
        results = await svc.run_target_batch(
            targets=[good_target, bad_target],
            run_id=uuid.uuid4(),
            adapter_registry=registry,
            browser_pool=pool,
        )

    svc.db.rollback.assert_awaited_once()
    svc.db.commit.assert_not_awaited()
    assert results["targets_failed"] == 1
    assert results["errors"] == ["target task failed"]


@pytest.mark.asyncio
async def test_pagination_timeout_aborts_crawl_without_hanging():
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
    registry, _fetch_fn = _registry_for_fetcher(
        fetch_result=SimpleNamespace(
            status_code=200,
            html="""
                <section class="job-listings">
                  <div class="job-card">
                    <h2><a href="/jobs/frontend-engineer">Frontend Engineer</a></h2>
                    <p class="location">Austin, TX</p>
                  </div>
                </section>
            """,
            headers={},
            content_hash="abc123",
            duration_ms=150,
        )
    )
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
        patch("app.scraping.service.evaluate_robots", _robots_allowed()),
        patch("app.scraping.execution.page_crawler.PageCrawler.crawl", side_effect=slow_crawl),
        patch("app.scraping.service.persist_jobs", AsyncMock(return_value=(1, 0))),
    ):
        svc.PAGINATION_TIMEOUT_S = 0.01
        results = await svc.run_target_batch(
            targets=[target],
            run_id=uuid.uuid4(),
            adapter_registry=registry,
            browser_pool=pool,
        )

    svc.db.commit.assert_awaited_once()
    assert results["targets_succeeded"] == 1
    assert results["targets_failed"] == 0
