import logging
from datetime import datetime
from typing import Optional

import httpx

from backend.config import get_settings
from backend.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class SerpApiScraper(BaseScraper):
    source_name = "serpapi"
    rate_limit_delay = 1.0

    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://serpapi.com/search.json"

    async def fetch_jobs(
        self, query: str, location: str, limit: int = 100
    ) -> list[dict]:
        if not self.settings.SERPAPI_KEY:
            logger.warning("SerpApi key not configured, skipping")
            return []

        all_jobs = []
        start = 0
        page_size = 10

        async with httpx.AsyncClient(timeout=30.0) as client:
            while len(all_jobs) < limit:
                params = {
                    "engine": "google_jobs",
                    "q": query,
                    "location": location,
                    "hl": "en",
                    "gl": "us",
                    "start": start,
                    "api_key": self.settings.SERPAPI_KEY,
                }

                try:
                    resp = await client.get(self.base_url, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                except httpx.HTTPError as e:
                    logger.error(f"SerpApi request failed: {e}")
                    break

                jobs_results = data.get("jobs_results", [])
                if not jobs_results:
                    break

                for job in jobs_results:
                    normalized = self._normalize_serpapi(job)
                    if normalized:
                        all_jobs.append(normalized)

                start += page_size
                await self._rate_limit()

                if len(jobs_results) < page_size:
                    break

        logger.info(f"SerpApi: fetched {len(all_jobs)} jobs for '{query}' in '{location}'")
        return all_jobs[:limit]

    def _normalize_serpapi(self, raw: dict) -> Optional[dict]:
        title = raw.get("title", "").strip()
        company = raw.get("company_name", "").strip()
        if not title or not company:
            return None

        location_str = raw.get("location", "")
        location_parts = self._parse_location(location_str)

        # Extract salary from detected_extensions
        extensions = raw.get("detected_extensions", {})
        salary_min = None
        salary_max = None
        salary_period = None
        if "salary" in extensions:
            salary_str = extensions["salary"]
            salary_min, salary_max, salary_period = self._parse_salary(salary_str)

        job_type = None
        if extensions.get("schedule_type"):
            schedule = extensions["schedule_type"].lower()
            if "full" in schedule:
                job_type = "full-time"
            elif "part" in schedule:
                job_type = "part-time"
            elif "contract" in schedule or "contractor" in schedule:
                job_type = "contract"
            elif "intern" in schedule:
                job_type = "internship"

        # Get apply URL
        apply_options = raw.get("apply_options", [])
        url = apply_options[0]["link"] if apply_options else raw.get("share_link", "")

        # Source hint from "via" field
        via = raw.get("via", "")

        description = raw.get("description", "")

        job_data = {
            "title": title,
            "company_name": company,
            "url": url,
            "description_raw": description,
            "description": description,
            "source": self.source_name,
            "job_type": job_type,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_period": salary_period,
            **location_parts,
        }

        return self.normalize(job_data)

    @staticmethod
    def _parse_salary(salary_str: str) -> tuple:
        import re
        salary_str = salary_str.replace(",", "").replace("$", "")
        numbers = re.findall(r"[\d.]+", salary_str)
        period = "annual"
        lower = salary_str.lower()
        if "hour" in lower or "/hr" in lower:
            period = "hourly"
        elif "month" in lower:
            period = "monthly"

        if len(numbers) >= 2:
            return float(numbers[0]), float(numbers[1]), period
        elif len(numbers) == 1:
            val = float(numbers[0])
            return val, val, period
        return None, None, None
