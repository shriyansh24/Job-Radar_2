"""Tests for CamoufoxBrowser adapter."""
from __future__ import annotations

import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scraping.execution.browser_port import BrowserPort, BrowserResult
from app.scraping.execution.camoufox_browser import CamoufoxBrowser


def test_implements_browser_port():
    assert issubclass(CamoufoxBrowser, BrowserPort)


def test_browser_name():
    b = CamoufoxBrowser()
    assert b.browser_name == "camoufox"


@pytest.mark.asyncio
async def test_render_when_camoufox_unavailable():
    """render() should raise RuntimeError when camoufox is not installed."""
    with patch(
        "app.scraping.execution.camoufox_browser.CAMOUFOX_AVAILABLE", False
    ):
        b = CamoufoxBrowser()
        with pytest.raises(RuntimeError, match="camoufox not installed"):
            await b.render("https://example.com")


@pytest.mark.asyncio
async def test_health_check_reflects_availability():
    b = CamoufoxBrowser()
    result = await b.health_check()
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_health_check_false_when_unavailable():
    with patch(
        "app.scraping.execution.camoufox_browser.CAMOUFOX_AVAILABLE", False
    ):
        b = CamoufoxBrowser()
        assert await b.health_check() is False


@pytest.mark.asyncio
async def test_render_returns_browser_result():
    """render() should return a BrowserResult with mocked camoufox."""
    html_content = "<html><body>Rendered by Camoufox</body></html>"

    mock_page = AsyncMock()
    mock_page.content.return_value = html_content
    mock_page.url = "https://example.com/final"

    mock_browser = AsyncMock()
    mock_browser.new_page.return_value = mock_page

    # AsyncCamoufox is used as async context manager
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_browser)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.scraping.execution.camoufox_browser.CAMOUFOX_AVAILABLE", True
    ), patch(
        "app.scraping.execution.camoufox_browser.AsyncCamoufox",
        return_value=mock_ctx,
    ):
        b = CamoufoxBrowser()
        result = await b.render("https://example.com")

    assert isinstance(result, BrowserResult)
    assert result.html == html_content
    assert result.status_code == 200
    assert result.url_final == "https://example.com/final"
    expected_hash = hashlib.sha256(html_content.encode()).hexdigest()[:64]
    assert result.content_hash == expected_hash
    assert result.duration_ms >= 0
    mock_page.goto.assert_called_once_with(
        "https://example.com", timeout=60000
    )


@pytest.mark.asyncio
async def test_render_with_wait_for_selector():
    """render() should call wait_for_selector when provided."""
    html_content = "<html><body><div id='jobs'>loaded</div></body></html>"

    mock_page = AsyncMock()
    mock_page.content.return_value = html_content
    mock_page.url = "https://example.com"

    mock_browser = AsyncMock()
    mock_browser.new_page.return_value = mock_page

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_browser)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.scraping.execution.camoufox_browser.CAMOUFOX_AVAILABLE", True
    ), patch(
        "app.scraping.execution.camoufox_browser.AsyncCamoufox",
        return_value=mock_ctx,
    ):
        b = CamoufoxBrowser()
        result = await b.render(
            "https://example.com",
            wait_for_selector="#jobs",
            timeout_s=30,
        )

    mock_page.wait_for_selector.assert_called_once_with(
        "#jobs", timeout=30000
    )
    assert result.html == html_content


@pytest.mark.asyncio
async def test_render_with_fingerprint_config():
    """render() should pass fingerprint config to AsyncCamoufox."""
    html_content = "<html><body>FP test</body></html>"
    fp_config = {"screen": {"width": 1920, "height": 1080}}

    mock_page = AsyncMock()
    mock_page.content.return_value = html_content
    mock_page.url = "https://example.com"

    mock_browser = AsyncMock()
    mock_browser.new_page.return_value = mock_page

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_browser)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.scraping.execution.camoufox_browser.CAMOUFOX_AVAILABLE", True
    ), patch(
        "app.scraping.execution.camoufox_browser.AsyncCamoufox",
        return_value=mock_ctx,
    ) as mock_async_camoufox:
        b = CamoufoxBrowser()
        await b.render("https://example.com", fingerprint=fp_config)

    mock_async_camoufox.assert_called_once_with(
        config=fp_config, headless=True
    )


@pytest.mark.asyncio
async def test_render_default_empty_fingerprint():
    """render() with no fingerprint should pass empty dict as config."""
    html_content = "<html><body>Default</body></html>"

    mock_page = AsyncMock()
    mock_page.content.return_value = html_content
    mock_page.url = "https://example.com"

    mock_browser = AsyncMock()
    mock_browser.new_page.return_value = mock_page

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_browser)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.scraping.execution.camoufox_browser.CAMOUFOX_AVAILABLE", True
    ), patch(
        "app.scraping.execution.camoufox_browser.AsyncCamoufox",
        return_value=mock_ctx,
    ) as mock_async_camoufox:
        b = CamoufoxBrowser()
        await b.render("https://example.com")

    mock_async_camoufox.assert_called_once_with(config={}, headless=True)


@pytest.mark.asyncio
async def test_render_propagates_exceptions():
    """Errors from camoufox should propagate to the caller."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(
        side_effect=TimeoutError("browser launch timeout")
    )
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.scraping.execution.camoufox_browser.CAMOUFOX_AVAILABLE", True
    ), patch(
        "app.scraping.execution.camoufox_browser.AsyncCamoufox",
        return_value=mock_ctx,
    ):
        b = CamoufoxBrowser()
        with pytest.raises(TimeoutError):
            await b.render("https://example.com")


@pytest.mark.asyncio
async def test_close_is_noop():
    b = CamoufoxBrowser()
    await b.close()  # Should not raise
