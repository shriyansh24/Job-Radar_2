from __future__ import annotations

import pytest

from app.scraping.execution.browser_port import BrowserPort, BrowserResult
from app.scraping.execution.extractor_port import ExtractorPort
from app.scraping.execution.fetcher_port import FetcherPort, FetchResult


def test_fetch_result_dataclass():
    r = FetchResult(
        html="<html>",
        status_code=200,
        headers={},
        url_final="https://example.com",
        duration_ms=100,
        content_hash="abc123",
    )
    assert r.html == "<html>"
    assert r.status_code == 200


def test_browser_result_dataclass():
    r = BrowserResult(
        html="<html>",
        status_code=200,
        url_final="https://example.com",
        duration_ms=500,
        content_hash="def456",
    )
    assert r.screenshot is None  # optional


def test_fetcher_port_is_abstract():
    """Cannot instantiate FetcherPort directly."""
    import pytest

    with pytest.raises(TypeError):
        FetcherPort()


def test_browser_port_is_abstract():
    import pytest

    with pytest.raises(TypeError):
        BrowserPort()


def test_extractor_port_is_abstract():
    with pytest.raises(TypeError):
        ExtractorPort()


class _SuperBrowserPort(BrowserPort):
    @property
    def browser_name(self) -> str:
        return super().browser_name

    async def render(
        self,
        url: str,
        timeout_s: int = 60,
        fingerprint=None,
        wait_for_selector=None,
    ):
        return await super().render(url, timeout_s, fingerprint, wait_for_selector)

    async def health_check(self) -> bool:
        return await super().health_check()


class _SuperFetcherPort(FetcherPort):
    @property
    def fetcher_name(self) -> str:
        return super().fetcher_name

    async def fetch(
        self,
        url: str,
        timeout_s: int = 30,
        user_agent: str | None = None,
    ) -> FetchResult:
        return await super().fetch(url, timeout_s, user_agent)

    async def health_check(self) -> bool:
        return await super().health_check()


class _SuperExtractorPort(ExtractorPort):
    async def extract_jobs(self, html: str, url: str):
        return await super().extract_jobs(html, url)

    async def to_markdown(self, html: str) -> str:
        return await super().to_markdown(html)


@pytest.mark.asyncio
async def test_browser_port_default_methods_raise_and_close_is_noop() -> None:
    port = _SuperBrowserPort()

    with pytest.raises(NotImplementedError):
        _ = port.browser_name
    with pytest.raises(NotImplementedError):
        await port.render("https://example.com")
    with pytest.raises(NotImplementedError):
        await port.health_check()
    assert await port.close() is None


@pytest.mark.asyncio
async def test_fetcher_port_default_methods_raise_and_close_is_noop() -> None:
    port = _SuperFetcherPort()

    with pytest.raises(NotImplementedError):
        _ = port.fetcher_name
    with pytest.raises(NotImplementedError):
        await port.fetch("https://example.com")
    with pytest.raises(NotImplementedError):
        await port.health_check()
    assert await port.close() is None


@pytest.mark.asyncio
async def test_extractor_port_default_methods_raise() -> None:
    port = _SuperExtractorPort()

    with pytest.raises(NotImplementedError):
        await port.extract_jobs("<html></html>", "https://example.com")
    with pytest.raises(NotImplementedError):
        await port.to_markdown("<html></html>")
