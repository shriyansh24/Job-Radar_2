"""Scraper implementations.

All scrapers implement the ScraperPort interface from app.scraping.port.
"""

from __future__ import annotations

from app.scraping.scrapers.ai_scraper import AIScraper
from app.scraping.scrapers.adaptive_parser import AdaptiveCareerParser
from app.scraping.scrapers.content_hasher import ContentHasher
from app.scraping.scrapers.detail_extractor import DetailPageExtractor
from app.scraping.scrapers.scrapingbee import ScrapingBeeScraper
from app.scraping.scrapers.scrapling import ScraplingScraper

__all__ = [
    "AIScraper",
    "AdaptiveCareerParser",
    "ContentHasher",
    "DetailPageExtractor",
    "ScrapingBeeScraper",
    "ScraplingScraper",
]
