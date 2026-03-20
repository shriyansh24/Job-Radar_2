"""Crawl4AI-based HTML-to-markdown extractor."""
from __future__ import annotations

import re

from app.scraping.execution.extractor_port import ExtractorPort
from app.scraping.port import ScrapedJob

try:
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.extraction_strategy import NoExtractionStrategy

    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False


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
        if not CRAWL4AI_AVAILABLE:
            # Fallback: strip tags with basic regex approach
            text = re.sub(r"<[^>]+>", "", html)
            return text.strip()

        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(
                url="about:blank",
                html_content=html,
                extraction_strategy=NoExtractionStrategy(),
            )
            return result.markdown or ""
