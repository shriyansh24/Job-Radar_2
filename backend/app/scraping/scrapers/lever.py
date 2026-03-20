from __future__ import annotations

import structlog

from app.scraping.port import ScrapedJob
from app.scraping.scrapers.base import BaseScraper

logger = structlog.get_logger()


class LeverScraper(BaseScraper):
    """Lever ATS job boards."""

    @property
    def source_name(self) -> str:
        return "lever"

    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        """Fetch from Lever postings API. query = company slug."""
        url = f"https://api.lever.co/v0/postings/{query}"
        params = {"mode": "json"}

        resp = await self.client.get(url, params=params)
        resp.raise_for_status()
        postings = resp.json()

        jobs: list[ScrapedJob] = []
        for item in postings:
            cats = item.get("categories", {})
            jobs.append(
                ScrapedJob(
                    title=item.get("text", ""),
                    company_name=query,
                    source=self.source_name,
                    source_url=item.get("hostedUrl"),
                    location=cats.get("location", ""),
                    remote_type=self._normalize_remote_type(cats.get("location", "")),
                    description_raw=item.get("descriptionPlain", ""),
                    experience_level=self._normalize_experience(cats.get("commitment")),
                    job_type=cats.get("commitment"),
                )
            )
        return jobs[:limit]

    async def health_check(self) -> bool:
        try:
            resp = await self.client.get(
                "https://api.lever.co/v0/postings/test", params={"mode": "json"}
            )
            return resp.status_code in (200, 404)
        except Exception:
            return False
