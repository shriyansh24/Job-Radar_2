"""Tests for NodriverBrowser adapter."""
from __future__ import annotations

import asyncio
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scraping.execution.browser_port import BrowserPort, BrowserResult
from app.scraping.execution.nodriver_browser import NodriverBrowser


def test_implements_browser_port():
    assert issubclass(NodriverBrowser, BrowserPort)


def test_browser_name():
    b = NodriverBrowser()
    assert b.browser_name == "nodriver"


def test_init_sets_browser_none_and_lock():
    """__init__ should set _browser to None and create an asyncio.Lock."""
    b = NodriverBrowser()
    assert b._browser is None
    assert isinstance(b._lock, asyncio.Lock)


@pytest.mark.asyncio
async def test_render_when_nodriver_unavailable():
    """render() should raise RuntimeError when nodriver is not installed."""
    with patch(
        "app.scraping.execution.nodriver_browser.NODRIVER_AVAILABLE", False
    ):
        b = NodriverBrowser()
        with pytest.raises(RuntimeError, match="nodriver not installed"):
            await b.render("https://example.com")


@pytest.mark.asyncio
async def test_health_check_reflects_availability():
    b = NodriverBrowser()
    result = await b.health_check()
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_health_check_false_when_unavailable():
    with patch(
        "app.scraping.execution.nodriver_browser.NODRIVER_AVAILABLE", False
    ):
        b = NodriverBrowser()
        assert await b.health_check() is False


@pytest.mark.asyncio
async def test_render_returns_browser_result():
    """render() should return a BrowserResult with mocked nodriver."""
    html_content = "<html><body>Rendered</body></html>"

    mock_page = AsyncMock()
    mock_page.get_content.return_value = html_content
    mock_page.url = "https://example.com/final"
    mock_page.sleep = AsyncMock()

    mock_browser = AsyncMock()
    mock_browser.get.return_value = mock_page
    mock_browser.stop = MagicMock()

    with (
        patch(
            "app.scraping.execution.nodriver_browser.NODRIVER_AVAILABLE", True
        ),
        patch(
            "app.scraping.execution.nodriver_browser.uc"
        ) as mock_uc,
    ):
        mock_uc.start = AsyncMock(return_value=mock_browser)

        b = NodriverBrowser()
        result = await b.render("https://example.com")

    assert isinstance(result, BrowserResult)
    assert result.html == html_content
    assert result.status_code == 200
    assert result.url_final == "https://example.com/final"
    expected_hash = hashlib.sha256(html_content.encode()).hexdigest()[:64]
    assert result.content_hash == expected_hash
    assert result.duration_ms >= 0
    # Browser should NOT be stopped — it is reused across calls
    mock_browser.stop.assert_not_called()


@pytest.mark.asyncio
async def test_render_with_wait_for_selector():
    """render() should use find() when wait_for_selector is provided."""
    html_content = "<html><body><div id='jobs'>loaded</div></body></html>"

    mock_page = AsyncMock()
    mock_page.get_content.return_value = html_content
    mock_page.url = "https://example.com"
    mock_page.find = AsyncMock()

    mock_browser = AsyncMock()
    mock_browser.get.return_value = mock_page
    mock_browser.stop = MagicMock()

    with (
        patch(
            "app.scraping.execution.nodriver_browser.NODRIVER_AVAILABLE", True
        ),
        patch(
            "app.scraping.execution.nodriver_browser.uc"
        ) as mock_uc,
    ):
        mock_uc.start = AsyncMock(return_value=mock_browser)

        b = NodriverBrowser()
        result = await b.render(
            "https://example.com",
            wait_for_selector="#jobs",
            timeout_s=30,
        )

    mock_page.find.assert_called_once_with("#jobs", timeout=30)
    mock_page.sleep.assert_not_called()
    assert result.html == html_content


@pytest.mark.asyncio
async def test_render_does_not_stop_browser_on_exception():
    """Browser should remain alive even if a render() call fails."""
    mock_browser = AsyncMock()
    mock_browser.get.side_effect = TimeoutError("page load timeout")
    mock_browser.stop = MagicMock()

    with (
        patch(
            "app.scraping.execution.nodriver_browser.NODRIVER_AVAILABLE", True
        ),
        patch(
            "app.scraping.execution.nodriver_browser.uc"
        ) as mock_uc,
    ):
        mock_uc.start = AsyncMock(return_value=mock_browser)

        b = NodriverBrowser()
        with pytest.raises(TimeoutError):
            await b.render("https://example.com")

    # Browser is persistent — it is NOT stopped on render failure
    mock_browser.stop.assert_not_called()


@pytest.mark.asyncio
async def test_get_browser_lazy_init():
    """_get_browser() should start browser once and reuse on subsequent calls."""
    mock_browser = AsyncMock()

    with (
        patch(
            "app.scraping.execution.nodriver_browser.NODRIVER_AVAILABLE", True
        ),
        patch(
            "app.scraping.execution.nodriver_browser.uc"
        ) as mock_uc,
    ):
        mock_uc.start = AsyncMock(return_value=mock_browser)

        b = NodriverBrowser()
        browser1 = await b._get_browser()
        browser2 = await b._get_browser()

    # uc.start() should be called exactly once
    assert mock_uc.start.await_count == 1
    assert browser1 is mock_browser
    assert browser2 is mock_browser


@pytest.mark.asyncio
async def test_render_reuses_browser_across_calls():
    """Multiple render() calls should reuse the same browser instance."""
    html_content = "<html><body>OK</body></html>"

    mock_page = AsyncMock()
    mock_page.get_content.return_value = html_content
    mock_page.url = "https://example.com"
    mock_page.sleep = AsyncMock()

    mock_browser = AsyncMock()
    mock_browser.get.return_value = mock_page

    with (
        patch(
            "app.scraping.execution.nodriver_browser.NODRIVER_AVAILABLE", True
        ),
        patch(
            "app.scraping.execution.nodriver_browser.uc"
        ) as mock_uc,
    ):
        mock_uc.start = AsyncMock(return_value=mock_browser)

        b = NodriverBrowser()
        await b.render("https://example.com/page1")
        await b.render("https://example.com/page2")

    # Browser started once, used twice
    assert mock_uc.start.await_count == 1
    assert mock_browser.get.await_count == 2


@pytest.mark.asyncio
async def test_close_stops_browser():
    """close() should stop the persistent browser and reset _browser to None."""
    mock_browser = MagicMock()
    mock_browser.stop = MagicMock()

    b = NodriverBrowser()
    b._browser = mock_browser

    await b.close()

    mock_browser.stop.assert_called_once()
    assert b._browser is None


@pytest.mark.asyncio
async def test_close_when_no_browser():
    """close() should be safe to call when no browser has been started."""
    b = NodriverBrowser()
    await b.close()  # Should not raise
    assert b._browser is None
