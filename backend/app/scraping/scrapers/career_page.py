from __future__ import annotations

import json
from datetime import datetime
from urllib.parse import urljoin

import structlog

from app.scraping.port import ScrapedJob
from app.scraping.scrapers.base import BaseScraper

logger = structlog.get_logger()


class CareerPageScraper(BaseScraper):
    """Scrapes individual company career pages using HTTP + HTML parsing."""

    @property
    def source_name(self) -> str:
        return "career_page"

    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        """query = career page URL. Fetches page, extracts job links."""
        from bs4 import BeautifulSoup

        resp = await self.client.get(query)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        jobs: list[ScrapedJob] = []

        # Strategy 1: JSON-LD structured data
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == "JobPosting":
                            jobs.append(self._parse_jsonld(item, query))
                elif data.get("@type") == "JobPosting":
                    jobs.append(self._parse_jsonld(data, query))
            except (json.JSONDecodeError, TypeError):
                continue

        # Strategy 2: Common CSS selectors for job listings
        if not jobs:
            for link in soup.find_all("a", href=True):
                href = link["href"]
                text = link.get_text(strip=True)
                if any(
                    kw in href.lower() for kw in ["/job/", "/position/", "/opening/", "/career/"]
                ):
                    if text and len(text) > 5:
                        jobs.append(
                            ScrapedJob(
                                title=text,
                                company_name="",  # Filled by caller
                                source=self.source_name,
                                source_url=urljoin(query, href),
                            )
                        )

        return jobs[:limit]

    def _parse_jsonld(self, data: dict, page_url: str) -> ScrapedJob:
        loc = data.get("jobLocation", {})
        if isinstance(loc, list):
            loc = loc[0] if loc else {}
        address = loc.get("address", {}) if isinstance(loc, dict) else {}

        location_parts = [
            address.get("addressLocality", ""),
            address.get("addressRegion", ""),
        ]
        location_str = ", ".join(p for p in location_parts if p)

        posted_at = None
        if data.get("datePosted"):
            try:
                posted_at = datetime.fromisoformat(data["datePosted"])
            except (ValueError, TypeError):
                pass

        return ScrapedJob(
            title=data.get("title", ""),
            company_name=data.get("hiringOrganization", {}).get("name", ""),
            source=self.source_name,
            source_url=data.get("url", page_url),
            location=location_str,
            description_raw=data.get("description", ""),
            posted_at=posted_at,
        )

    async def health_check(self) -> bool:
        return True  # No external API dependency
