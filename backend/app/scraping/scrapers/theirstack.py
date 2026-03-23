from __future__ import annotations

from datetime import datetime

import structlog

from app.scraping.port import ScrapedJob
from app.scraping.scrapers.base import BaseScraper

logger = structlog.get_logger()


class TheirStackScraper(BaseScraper):
    """TheirStack API for technology-focused job data."""

    @property
    def source_name(self) -> str:
        return "theirstack"

    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        if not self.settings.theirstack_api_key:
            logger.debug("theirstack_skipped", reason="no_api_key")
            return []

        url = "https://api.theirstack.com/v1/jobs/search"
        payload: dict[str, object] = {"query": query, "limit": limit}
        if location:
            payload["location"] = location

        headers = {"Authorization": f"Bearer {self.settings.theirstack_api_key}"}
        resp = await self.client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        jobs: list[ScrapedJob] = []
        for item in data.get("data", []):
            posted_at = None
            if item.get("date_posted"):
                try:
                    posted_at = datetime.fromisoformat(item["date_posted"])
                except (ValueError, TypeError):
                    pass

            # ATS ID: id from TheirStack result
            ats_job_id = str(item["id"]) if item.get("id") else None

            jobs.append(
                ScrapedJob(
                    title=item.get("job_title", ""),
                    company_name=item.get("company_name", ""),
                    source=self.source_name,
                    source_url=item.get("url"),
                    location=item.get("location"),
                    description_raw=item.get("description"),
                    posted_at=posted_at,
                    ats_job_id=ats_job_id,
                    ats_provider="theirstack",
                )
            )
        return jobs[:limit]

    async def health_check(self) -> bool:
        if not self.settings.theirstack_api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.settings.theirstack_api_key}"}
            resp = await self.client.get("https://api.theirstack.com/v1/health", headers=headers)
            return resp.status_code == 200
        except Exception:
            return False
