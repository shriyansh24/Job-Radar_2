from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

import app.workers.scraping_worker as scraping_worker


@pytest.mark.asyncio
async def test_run_scheduled_scrape_reraises_service_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = Mock()
    service = Mock()
    service.run_scrape = AsyncMock(side_effect=RuntimeError("scrape failed"))
    service.close = AsyncMock()
    profile = SimpleNamespace(
        user_id="user-123",
        search_queries=[{"query": "python", "location": "Austin"}],
    )
    monkeypatch.setattr(scraping_worker, "Settings", Mock(return_value=object()))
    monkeypatch.setattr(scraping_worker, "ScrapingService", Mock(return_value=service))
    monkeypatch.setattr(scraping_worker, "logger", logger)

    class _FakeSelect:
        def limit(self, *_args: object, **_kwargs: object) -> "_FakeSelect":
            return self

    monkeypatch.setattr("sqlalchemy.select", lambda *_args, **_kwargs: _FakeSelect())

    class _FakeSession:
        async def scalar(self, _query: object) -> object:
            return profile

    @asynccontextmanager
    async def _profile_session_factory():
        yield _FakeSession()

    monkeypatch.setattr(scraping_worker, "async_session_factory", _profile_session_factory)

    with pytest.raises(RuntimeError, match="scrape failed"):
        await scraping_worker.run_scheduled_scrape()

    service.close.assert_awaited_once()
    logger.exception.assert_called_once_with("scheduled_scrape_failed")


@pytest.mark.asyncio
async def test_run_target_batch_job_reraises_batch_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = Mock()
    settings = object()
    target = SimpleNamespace(source_kind="career_page", enabled=True, quarantined=False)
    db = Mock()
    db.scalars = AsyncMock(return_value=SimpleNamespace(all=lambda: [target]))

    @asynccontextmanager
    async def _session_factory():
        yield db

    monkeypatch.setattr(scraping_worker, "async_session_factory", _session_factory)
    monkeypatch.setattr(scraping_worker, "Settings", Mock(return_value=settings))
    monkeypatch.setattr(scraping_worker, "logger", logger)
    monkeypatch.setattr(
        "app.scraping.control.scheduler.select_due_targets",
        Mock(side_effect=RuntimeError("due-target selection failed")),
    )

    with pytest.raises(RuntimeError, match="due-target selection failed"):
        await scraping_worker.run_target_batch_job()

    logger.exception.assert_called_once_with(
        "target_batch_job_failed",
        source_kind="career_page",
    )
