"""Crawl4AI-based HTML-to-markdown extractor."""

from __future__ import annotations

import html
import re

import structlog

from app.scraping.execution.extractor_port import ExtractorPort
from app.scraping.port import ScrapedJob

try:
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.extraction_strategy import NoExtractionStrategy

    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False

logger = structlog.get_logger()


class Crawl4AIExtractor(ExtractorPort):
    """Extracts job data and converts HTML to markdown using Crawl4AI.

    When Crawl4AI is not installed, falls back to basic HTML tag stripping
    for the ``to_markdown`` method.
    """

    async def extract_jobs(self, html: str, url: str) -> list[ScrapedJob]:
        """Extract jobs from HTML.

        Returns an empty list because job extraction is handled by
        ATS-specific parsers, not this generic extractor.  The method
        exists to satisfy the :class:`ExtractorPort` interface.
        """
        return []

    async def to_markdown(self, html: str) -> str:
        """Convert HTML to clean markdown.

        Uses Crawl4AI when available; otherwise falls back to a simple
        regex-based tag stripper.
        """
        if not html.strip():
            return ""

        if not CRAWL4AI_AVAILABLE:
            return self._fallback_markdown(html)

        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(
                    url="raw:",
                    html_content=html,
                    extraction_strategy=NoExtractionStrategy(),
                )
        except Exception as exc:
            logger.warning(
                "crawl4ai_markdown_fallback",
                subsystem="scraping",
                operation="html_to_markdown",
                reason=str(exc),
                html_length=len(html),
            )
            return self._fallback_markdown(html)

        markdown = (result.markdown or "").strip()
        if markdown:
            return markdown
        return self._fallback_markdown(html)

    def _fallback_markdown(self, html_content: str) -> str:
        text = re.sub(r"<[^>]+>", " ", html_content)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
