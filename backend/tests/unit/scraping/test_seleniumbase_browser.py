"""Tests for SeleniumBaseBrowser adapter."""
from __future__ import annotations

import hashlib
from unittest.mock import MagicMock, patch

import pytest

from app.scraping.execution.browser_port import BrowserPort, BrowserResult
from app.scraping.execution.seleniumbase_browser import SeleniumBaseBrowser


def test_implements_browser_port():
    assert issubclass(SeleniumBaseBrowser, BrowserPort)


def test_browser_name():
    b = SeleniumBaseBrowser()
    assert b.browser_name == "seleniumbase"


@pytest.mark.asyncio
async def test_render_when_seleniumbase_unavailable():
    """render() should raise RuntimeError when seleniumbase is not installed."""
    with patch(
        "app.scraping.execution.seleniumbase_browser.SELENIUMBASE_AVAILABLE",
        False,
    ):
        b = SeleniumBaseBrowser()
        with pytest.raises(RuntimeError, match="seleniumbase not installed"):
            await b.render("https://example.com")


@pytest.mark.asyncio
async def test_health_check_reflects_availability():
    b = SeleniumBaseBrowser()
    result = await b.health_check()
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_health_check_false_when_unavailable():
    with patch(
        "app.scraping.execution.seleniumbase_browser.SELENIUMBASE_AVAILABLE",
        False,
    ):
        b = SeleniumBaseBrowser()
        assert await b.health_check() is False


@pytest.mark.asyncio
async def test_render_returns_browser_result():
    """render() should return a BrowserResult with mocked seleniumbase."""
    html_content = "<html><body>Rendered by SeleniumBase</body></html>"

    mock_driver = MagicMock()
    mock_driver.page_source = html_content

    with patch(
        "app.scraping.execution.seleniumbase_browser.SELENIUMBASE_AVAILABLE",
        True,
    ), patch(
        "app.scraping.execution.seleniumbase_browser._import_driver",
        return_value=MagicMock(return_value=mock_driver),
    ):
        b = SeleniumBaseBrowser()
        result = await b.render("https://example.com")

    assert isinstance(result, BrowserResult)
    assert result.html == html_content
    assert result.status_code == 200
    assert result.url_final == "https://example.com"
    expected_hash = hashlib.sha256(html_content.encode()).hexdigest()[:64]
    assert result.content_hash == expected_hash
    assert result.duration_ms >= 0
    mock_driver.get.assert_called_once_with("https://example.com")
    mock_driver.quit.assert_called_once()


@pytest.mark.asyncio
async def test_render_with_wait_for_selector():
    """render() should call wait_for_element when wait_for_selector is given."""
    html_content = "<html><body><div id='jobs'>loaded</div></body></html>"

    mock_driver = MagicMock()
    mock_driver.page_source = html_content

    with patch(
        "app.scraping.execution.seleniumbase_browser.SELENIUMBASE_AVAILABLE",
        True,
    ), patch(
        "app.scraping.execution.seleniumbase_browser._import_driver",
        return_value=MagicMock(return_value=mock_driver),
    ):
        b = SeleniumBaseBrowser()
        result = await b.render(
            "https://example.com",
            wait_for_selector="#jobs",
            timeout_s=30,
        )

    mock_driver.wait_for_element.assert_called_once_with("#jobs", timeout=30)
    assert result.html == html_content


@pytest.mark.asyncio
async def test_render_quits_driver_on_exception():
    """Driver should be quit even if rendering fails."""
    mock_driver = MagicMock()
    mock_driver.get.side_effect = TimeoutError("page load timeout")

    with patch(
        "app.scraping.execution.seleniumbase_browser.SELENIUMBASE_AVAILABLE",
        True,
    ), patch(
        "app.scraping.execution.seleniumbase_browser._import_driver",
        return_value=MagicMock(return_value=mock_driver),
    ):
        b = SeleniumBaseBrowser()
        with pytest.raises(TimeoutError):
            await b.render("https://example.com")

    mock_driver.quit.assert_called_once()


@pytest.mark.asyncio
async def test_close_is_noop():
    b = SeleniumBaseBrowser()
    await b.close()  # Should not raise
