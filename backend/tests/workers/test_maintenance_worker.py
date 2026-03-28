from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock

import pytest

import app.workers.maintenance_worker as maintenance_worker


@pytest.mark.asyncio
async def test_run_cleanup_reraises_database_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = Mock()
    db.execute = AsyncMock(side_effect=RuntimeError("cleanup exploded"))
    db.commit = AsyncMock()
    logger = Mock()

    @asynccontextmanager
    async def _session_factory():
        yield db

    monkeypatch.setattr(maintenance_worker, "async_session_factory", _session_factory)
    monkeypatch.setattr(maintenance_worker, "logger", logger)

    with pytest.raises(RuntimeError, match="cleanup exploded"):
        await maintenance_worker.run_cleanup()

    logger.exception.assert_called_once_with("cleanup_failed")
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_source_health_check_raises_when_sources_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = Mock()
    settings = object()

    def _scraper(healthy: bool) -> Mock:
        scraper = Mock()
        scraper.health_check = AsyncMock(return_value=healthy)
        scraper.close = AsyncMock()
        return scraper

    scrapers = {
        "serpapi": _scraper(False),
        "greenhouse": _scraper(True),
        "lever": _scraper(False),
        "ashby": _scraper(True),
        "theirstack": _scraper(True),
    }

    monkeypatch.setattr(maintenance_worker, "Settings", Mock(return_value=settings))
    monkeypatch.setattr(
        "app.scraping.scrapers.serpapi.SerpAPIScraper",
        lambda _settings: scrapers["serpapi"],
    )
    monkeypatch.setattr(
        "app.scraping.scrapers.greenhouse.GreenhouseScraper",
        lambda _settings: scrapers["greenhouse"],
    )
    monkeypatch.setattr(
        "app.scraping.scrapers.lever.LeverScraper",
        lambda _settings: scrapers["lever"],
    )
    monkeypatch.setattr(
        "app.scraping.scrapers.ashby.AshbyScraper",
        lambda _settings: scrapers["ashby"],
    )
    monkeypatch.setattr(
        "app.scraping.scrapers.theirstack.TheirStackScraper",
        lambda _settings: scrapers["theirstack"],
    )
    monkeypatch.setattr(maintenance_worker, "logger", logger)

    with pytest.raises(RuntimeError, match="lever, serpapi|serpapi, lever"):
        await maintenance_worker.run_source_health_check()

    for scraper in scrapers.values():
        scraper.close.assert_awaited_once()
    assert logger.info.call_count == 5
