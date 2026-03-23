"""Tests for ScraplingFetcher dual-mode adapter."""

from __future__ import annotations

import hashlib
from unittest.mock import MagicMock, patch

import pytest

from app.scraping.execution.browser_port import BrowserPort, BrowserResult
from app.scraping.execution.fetcher_port import FetcherPort, FetchResult
from app.scraping.execution.scrapling_fetcher import ScraplingFetcher


def test_implements_both_ports():
    f = ScraplingFetcher()
    assert isinstance(f, FetcherPort)
    assert isinstance(f, BrowserPort)


def test_fetcher_name():
    f = ScraplingFetcher()
    assert f.fetcher_name == "scrapling_fast"
    assert f.browser_name == "scrapling_stealth"


@pytest.mark.asyncio
async def test_health_check_reflects_availability():
    """health_check returns whether scrapling is importable."""
    f = ScraplingFetcher()
    result = await f.health_check()
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_fetch_when_scrapling_unavailable():
    """fetch() should raise RuntimeError when scrapling is not installed."""
    with patch("app.scraping.execution.scrapling_fetcher.SCRAPLING_AVAILABLE", False):
        f = ScraplingFetcher()
        with pytest.raises(RuntimeError, match="scrapling not installed"):
            await f.fetch("https://example.com")


@pytest.mark.asyncio
async def test_render_when_scrapling_unavailable():
    """render() should raise RuntimeError when scrapling is not installed."""
    with patch("app.scraping.execution.scrapling_fetcher.SCRAPLING_AVAILABLE", False):
        f = ScraplingFetcher()
        with pytest.raises(RuntimeError, match="scrapling not installed"):
            await f.render("https://example.com")


@pytest.mark.asyncio
async def test_fetch_returns_fetch_result():
    """fetch() should return a proper FetchResult with mocked Fetcher."""
    mock_resp = MagicMock()
    mock_resp.text = "<html>fast</html>"
    mock_resp.status_code = 200

    mock_fetcher_cls = MagicMock()
    mock_fetcher_instance = MagicMock()
    mock_fetcher_instance.get.return_value = mock_resp
    mock_fetcher_cls.return_value = mock_fetcher_instance

    with (
        patch("app.scraping.execution.scrapling_fetcher.SCRAPLING_AVAILABLE", True),
        patch("app.scraping.execution.scrapling_fetcher.Fetcher", mock_fetcher_cls),
    ):
        f = ScraplingFetcher()
        result = await f.fetch("https://example.com", timeout_s=15)

    assert isinstance(result, FetchResult)
    assert result.html == "<html>fast</html>"
    assert result.status_code == 200
    expected_hash = hashlib.sha256(b"<html>fast</html>").hexdigest()[:64]
    assert result.content_hash == expected_hash
    assert result.duration_ms >= 0


@pytest.mark.asyncio
async def test_render_returns_browser_result():
    """render() should return a BrowserResult with mocked StealthyFetcher."""
    mock_resp = MagicMock()
    mock_resp.text = "<html>stealth</html>"

    mock_stealth_cls = MagicMock()
    mock_stealth_instance = MagicMock()
    mock_stealth_instance.fetch.return_value = mock_resp
    mock_stealth_cls.return_value = mock_stealth_instance

    with (
        patch("app.scraping.execution.scrapling_fetcher.SCRAPLING_AVAILABLE", True),
        patch(
            "app.scraping.execution.scrapling_fetcher.StealthyFetcher",
            mock_stealth_cls,
        ),
    ):
        f = ScraplingFetcher()
        result = await f.render("https://example.com")

    assert isinstance(result, BrowserResult)
    assert result.html == "<html>stealth</html>"
    assert result.status_code == 200
    expected_hash = hashlib.sha256(b"<html>stealth</html>").hexdigest()[:64]
    assert result.content_hash == expected_hash


@pytest.mark.asyncio
async def test_close_is_noop():
    f = ScraplingFetcher()
    await f.close()  # Should not raise
