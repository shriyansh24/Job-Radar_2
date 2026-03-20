"""Tests for Crawl4AI HTML-to-markdown extractor adapter."""
from __future__ import annotations

import pytest

from app.scraping.execution.crawl4ai_extractor import Crawl4AIExtractor
from app.scraping.execution.extractor_port import ExtractorPort


def test_implements_extractor_port():
    """Crawl4AIExtractor must be a subclass of ExtractorPort."""
    assert issubclass(Crawl4AIExtractor, ExtractorPort)


def test_extractor_has_required_methods():
    """Verify extract_jobs and to_markdown methods exist and are callable."""
    e = Crawl4AIExtractor()
    assert hasattr(e, "extract_jobs")
    assert hasattr(e, "to_markdown")
    assert callable(e.extract_jobs)
    assert callable(e.to_markdown)


@pytest.mark.asyncio
async def test_extract_jobs_returns_empty_list():
    """extract_jobs returns [] because job extraction is handled by ATS parsers."""
    e = Crawl4AIExtractor()
    result = await e.extract_jobs("<html><body>Jobs here</body></html>", "https://example.com")
    assert result == []
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_to_markdown_fallback_strips_tags():
    """When Crawl4AI is not installed, fallback strips HTML tags."""
    e = Crawl4AIExtractor()
    html = "<html><body><h1>Title</h1><p>Hello world</p></body></html>"
    result = await e.to_markdown(html)
    assert "<h1>" not in result
    assert "<p>" not in result
    assert "Title" in result
    assert "Hello world" in result


@pytest.mark.asyncio
async def test_to_markdown_fallback_handles_empty_html():
    """Fallback handles empty HTML gracefully."""
    e = Crawl4AIExtractor()
    result = await e.to_markdown("")
    assert result == ""


@pytest.mark.asyncio
async def test_to_markdown_fallback_handles_plain_text():
    """Fallback passes through plain text without tags."""
    e = Crawl4AIExtractor()
    result = await e.to_markdown("Just plain text")
    assert result == "Just plain text"
