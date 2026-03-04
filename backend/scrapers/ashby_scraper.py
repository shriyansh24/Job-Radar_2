import logging
from datetime import datetime
from typing import Optional

import httpx

from backend.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class AshbyScraper(BaseScraper):
    source_name = "ashby"
    rate_limit_delay = 0.5

    BASE_URL = "https://api.ashbyhq.com/posting-api/job-board"

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
                    url = f"{self.BASE_URL}/{slug}?includeCompensation=true"
                    resp = await client.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                except httpx.HTTPError as e:
                    logger.error(f"Ashby [{slug}]: request failed: {e}")
                    await self._rate_limit()
                    continue

                postings = data.get("jobPostings", data.get("jobs", []))
                for job in postings:
                    normalized = self._normalize_ashby(job, slug)
                    if normalized:
                        all_jobs.append(normalized)

                logger.info(f"Ashby [{slug}]: found {len(postings)} jobs")
                await self._rate_limit()

        logger.info(f"Ashby: total {len(all_jobs)} jobs from {len(slugs)} boards")
        return all_jobs[:limit]

    def _normalize_ashby(self, raw: dict, slug: str) -> Optional[dict]:
        title = raw.get("title", "").strip()
        if not title:
            return None

        location_str = raw.get("locationName", raw.get("location", ""))
        location_parts = self._parse_location(location_str)

        employment_type = raw.get("employmentType", "")
        job_type = None
        if employment_type:
            lower = employment_type.lower()
            if "full" in lower:
                job_type = "full-time"
            elif "part" in lower:
                job_type = "part-time"
            elif "contract" in lower:
                job_type = "contract"
            elif "intern" in lower:
                job_type = "internship"

        published_at = raw.get("publishedAt")
        posted_at = None
        if published_at:
            try:
                posted_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # Parse compensation
        salary_min = None
        salary_max = None
        salary_period = None
        compensation = raw.get("compensation")
        if compensation:
            components = compensation.get("summaryComponents", [])
            for comp in components:
                if comp.get("minValue") is not None:
                    salary_min = comp["minValue"]
                if comp.get("maxValue") is not None:
                    salary_max = comp["maxValue"]
                if comp.get("interval"):
                    salary_period = comp["interval"].lower()

        team = raw.get("teamName", "")

        job_data = {
            "title": title,
            "company_name": slug.replace("-", " ").title(),
            "company_domain": f"{slug}.com",
            "url": raw.get("applicationLink", raw.get("jobUrl", "")),
            "description_raw": raw.get("descriptionHtml", ""),
            "description": raw.get("descriptionHtml", ""),
            "source": self.source_name,
            "posted_at": posted_at,
            "department": team,
            "job_type": job_type,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_period": salary_period,
            **location_parts,
        }

        return self.normalize(job_data)
