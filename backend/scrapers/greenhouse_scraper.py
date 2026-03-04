import logging
from datetime import datetime
from typing import Optional

import httpx

from backend.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class GreenhouseScraper(BaseScraper):
    source_name = "greenhouse"
    rate_limit_delay = 0.5

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    async def fetch_jobs(
        self, query: str, location: str, limit: int = 100, slugs: list[str] = None
    ) -> list[dict]:
        if not slugs:
            slugs = []

        all_jobs = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for slug in slugs:
                if len(all_jobs) >= limit:
                    break
                try:
                    url = f"{self.BASE_URL}/{slug}/jobs?content=true"
                    resp = await client.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                except httpx.HTTPError as e:
                    logger.error(f"Greenhouse [{slug}]: request failed: {e}")
                    await self._rate_limit()
                    continue

                jobs_list = data.get("jobs", [])
                for job in jobs_list:
                    normalized = self._normalize_greenhouse(job, slug)
                    if normalized:
                        all_jobs.append(normalized)

                logger.info(
                    f"Greenhouse [{slug}]: found {len(jobs_list)} jobs"
                )
                await self._rate_limit()

        logger.info(f"Greenhouse: total {len(all_jobs)} jobs from {len(slugs)} boards")
        return all_jobs[:limit]

    def _normalize_greenhouse(self, raw: dict, slug: str) -> Optional[dict]:
        title = raw.get("title", "").strip()
        if not title:
            return None

        location_str = raw.get("location", {}).get("name", "")
        location_parts = self._parse_location(location_str)

        content_html = raw.get("content", "")
        updated_at = raw.get("updated_at")
        posted_at = None
        if updated_at:
            try:
                posted_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        departments = raw.get("departments", [])
        department = departments[0]["name"] if departments else None

        job_data = {
            "title": title,
            "company_name": slug.replace("-", " ").title(),
            "company_domain": f"{slug}.com",
            "url": raw.get("absolute_url", ""),
            "description_raw": content_html,
            "description": content_html,
            "source": self.source_name,
            "posted_at": posted_at,
            "department": department,
            **location_parts,
        }

        return self.normalize(job_data)
