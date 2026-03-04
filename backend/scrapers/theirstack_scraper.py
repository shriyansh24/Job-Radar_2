import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx

from backend.config import get_settings
from backend.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class TheirStackScraper(BaseScraper):
    source_name = "theirstack"
    rate_limit_delay = 0.5

    BASE_URL = "https://api.theirstack.com/v1/jobs/search"

    def __init__(self):
        self.settings = get_settings()

    async def fetch_jobs(
        self, query: str, location: str, limit: int = 100
    ) -> list[dict]:
        if not self.settings.THEIRSTACK_KEY:
            logger.warning("TheirStack key not configured, skipping")
            return []

        all_jobs = []
        page = 0
        page_size = min(limit, 50)

        async with httpx.AsyncClient(timeout=30.0) as client:
            while len(all_jobs) < limit:
                headers = {
                    "Authorization": f"Bearer {self.settings.THEIRSTACK_KEY}",
                    "Content-Type": "application/json",
                }
                params = {
                    "q": query,
                    "location": location,
                    "date_posted_after": (
                        datetime.utcnow() - timedelta(days=7)
                    ).strftime("%Y-%m-%d"),
                    "limit": page_size,
                    "offset": page * page_size,
                }

                try:
                    resp = await client.get(
                        self.BASE_URL, params=params, headers=headers
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except httpx.HTTPError as e:
                    logger.error(f"TheirStack request failed: {e}")
                    break

                jobs_data = data.get("data", data.get("jobs", []))
                if not jobs_data:
                    break

                for job in jobs_data:
                    normalized = self._normalize_theirstack(job)
                    if normalized:
                        all_jobs.append(normalized)

                page += 1
                await self._rate_limit()

                if len(jobs_data) < page_size:
                    break

        logger.info(
            f"TheirStack: fetched {len(all_jobs)} jobs for '{query}' in '{location}'"
        )
        return all_jobs[:limit]

    def _normalize_theirstack(self, raw: dict) -> Optional[dict]:
        title = raw.get("title", raw.get("job_title", "")).strip()
        company = raw.get("company_name", raw.get("company", "")).strip()
        if not title or not company:
            return None

        location_str = raw.get("location", "")
        location_parts = self._parse_location(location_str)

        posted_at = None
        date_str = raw.get("date_posted", raw.get("published_at"))
        if date_str:
            try:
                posted_at = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        job_data = {
            "title": title,
            "company_name": company,
            "company_domain": raw.get("company_domain"),
            "url": raw.get("url", raw.get("job_url", "")),
            "description_raw": raw.get("description", ""),
            "description": raw.get("description", ""),
            "source": self.source_name,
            "posted_at": posted_at,
            "salary_min": raw.get("salary_min"),
            "salary_max": raw.get("salary_max"),
            "salary_currency": raw.get("salary_currency", "USD"),
            **location_parts,
        }

        return self.normalize(job_data)
