"""Tests for CloudscraperFetcher adapter."""

from __future__ import annotations

import hashlib
from unittest.mock import MagicMock, patch

import pytest

from app.scraping.execution.cloudscraper_fetcher import CloudscraperFetcher
from app.scraping.execution.fetcher_port import FetcherPort, FetchResult


def test_implements_fetcher_port():
    assert issubclass(CloudscraperFetcher, FetcherPort)


def test_fetcher_name():
    f = CloudscraperFetcher()
    assert f.fetcher_name == "cloudscraper"


@pytest.mark.asyncio
async def test_fetch_returns_fetch_result():
    """fetch() should return a proper FetchResult with correct fields."""
    mock_resp = MagicMock()
    mock_resp.text = "<html><body>Hello</body></html>"
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.url = "https://example.com/final"

    mock_scraper = MagicMock()
    mock_scraper.get.return_value = mock_resp

    with patch("app.scraping.execution.cloudscraper_fetcher.cs") as mock_cs:
        mock_cs.create_scraper.return_value = mock_scraper

        f = CloudscraperFetcher()
        result = await f.fetch("https://example.com", timeout_s=10)

    assert isinstance(result, FetchResult)
    assert result.html == "<html><body>Hello</body></html>"
    assert result.status_code == 200
    assert result.url_final == "https://example.com/final"
    assert (
        result.content_hash == hashlib.sha256(b"<html><body>Hello</body></html>").hexdigest()[:64]
    )
    assert result.duration_ms >= 0
    assert result.headers == {"Content-Type": "text/html"}
    mock_scraper.close.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_sets_user_agent():
    """fetch() should set user-agent header when provided."""
    mock_resp = MagicMock()
    mock_resp.text = "ok"
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.url = "https://example.com"

    mock_scraper = MagicMock()
    mock_scraper.get.return_value = mock_resp
    mock_scraper.headers = {}

    with patch("app.scraping.execution.cloudscraper_fetcher.cs") as mock_cs:
        mock_cs.create_scraper.return_value = mock_scraper

        f = CloudscraperFetcher()
        await f.fetch("https://example.com", user_agent="TestBot/1.0")

    assert mock_scraper.headers["User-Agent"] == "TestBot/1.0"


@pytest.mark.asyncio
async def test_fetch_closes_scraper_on_exception():
    """Scraper session should be closed even if the request fails."""
    mock_scraper = MagicMock()
    mock_scraper.get.side_effect = ConnectionError("refused")

    with patch("app.scraping.execution.cloudscraper_fetcher.cs") as mock_cs:
        mock_cs.create_scraper.return_value = mock_scraper

        f = CloudscraperFetcher()
        with pytest.raises(ConnectionError):
            await f.fetch("https://example.com")

    mock_scraper.close.assert_called_once()


@pytest.mark.asyncio
async def test_health_check_returns_true():
    f = CloudscraperFetcher()
    assert await f.health_check() is True


@pytest.mark.asyncio
async def test_close_is_noop():
    f = CloudscraperFetcher()
    await f.close()  # Should not raise
