import logging
from datetime import datetime
from typing import Optional

import httpx

from backend.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class LeverScraper(BaseScraper):
    source_name = "lever"
    rate_limit_delay = 0.5

    BASE_URL = "https://api.lever.co/v0/postings"

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
                    url = f"{self.BASE_URL}/{slug}?mode=json"
                    resp = await client.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                except httpx.HTTPError as e:
                    logger.error(f"Lever [{slug}]: request failed: {e}")
                    await self._rate_limit()
                    continue

                if not isinstance(data, list):
                    data = []

                for job in data:
                    normalized = self._normalize_lever(job, slug)
                    if normalized:
                        all_jobs.append(normalized)

                logger.info(f"Lever [{slug}]: found {len(data)} jobs")
                await self._rate_limit()

        logger.info(f"Lever: total {len(all_jobs)} jobs from {len(slugs)} boards")
        return all_jobs[:limit]

    def _normalize_lever(self, raw: dict, slug: str) -> Optional[dict]:
        title = raw.get("text", "").strip()
        if not title:
            return None

        categories = raw.get("categories", {})
        location_str = categories.get("location", "")
        location_parts = self._parse_location(location_str)

        team = categories.get("team", "")
        commitment = categories.get("commitment", "")

        created_at = raw.get("createdAt")
        posted_at = None
        if created_at:
            try:
                posted_at = datetime.fromtimestamp(created_at / 1000)
            except (ValueError, TypeError, OSError):
                pass

        job_type = None
        if commitment:
            lower = commitment.lower()
            if "full" in lower:
                job_type = "full-time"
            elif "part" in lower:
                job_type = "part-time"
            elif "contract" in lower:
                job_type = "contract"
            elif "intern" in lower:
                job_type = "internship"

        job_data = {
            "title": title,
            "company_name": slug.replace("-", " ").title(),
            "company_domain": f"{slug}.com",
            "url": raw.get("hostedUrl", ""),
            "description_raw": raw.get("description", ""),
            "description": raw.get("descriptionPlain", raw.get("description", "")),
            "source": self.source_name,
            "posted_at": posted_at,
            "department": team,
            "job_type": job_type,
            **location_parts,
        }

        return self.normalize(job_data)
