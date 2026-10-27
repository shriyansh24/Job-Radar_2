from __future__ import annotations

import structlog

from app.scraping.port import ScrapedJob
from app.scraping.scrapers.base import BaseScraper

logger = structlog.get_logger()


class ApifyScraper(BaseScraper):
    """Apify actors for LinkedIn/Indeed scraping."""

    @property
    def source_name(self) -> str:
        return "apify"

    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        if not self.settings.apify_api_key:
            logger.debug("apify_skipped", reason="no_api_key")
            return []

        url = "https://api.apify.com/v2/acts/johnvc~linkedin-jobs-api/run-sync-get-dataset-items"
        params = {"token": self.settings.apify_api_key}
        payload = {
            "keyword": query,
            "location": location or "United States",
            "maxJobs": limit,
        }

        resp = await self.client.post(url, json=payload, params=params, timeout=120.0)
        resp.raise_for_status()
        items = resp.json()

        jobs: list[ScrapedJob] = []
        for item in items:
            if item.get("error_message"):
                logger.warning(
                    "apify_item_error",
                    error_type=item.get("error_type"),
                    error=item.get("error_message"),
                )
                continue
            jobs.append(
                ScrapedJob(
                    title=item.get("title", ""),
                    company_name=item.get("companyName", ""),
                    source=self.source_name,
                    source_url=item.get("jobUrl"),
                    location=item.get("location"),
                    description_raw=item.get("description"),
                )
            )
        return jobs[:limit]

    async def health_check(self) -> bool:
        if not self.settings.apify_api_key:
            return False
        try:
            resp = await self.client.get(
                "https://api.apify.com/v2/users/me",
                params={"token": self.settings.apify_api_key},
            )
            return resp.status_code == 200
        except Exception:
            return False
