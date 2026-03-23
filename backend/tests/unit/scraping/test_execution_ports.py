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
    import pytest

    with pytest.raises(TypeError):
        ExtractorPort()
