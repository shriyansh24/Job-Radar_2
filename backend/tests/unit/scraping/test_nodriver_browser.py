"""Tests for NodriverBrowser adapter."""
from __future__ import annotations

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
    mock_browser.stop.assert_called_once()


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
async def test_render_stops_browser_on_exception():
    """Browser should be stopped even if rendering fails."""
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

    mock_browser.stop.assert_called_once()


@pytest.mark.asyncio
async def test_close_is_noop():
    b = NodriverBrowser()
    await b.close()  # Should not raise
