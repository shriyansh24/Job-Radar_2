from __future__ import annotations

import structlog

from app.scraping.port import ScrapedJob
from app.scraping.scrapers.base import BaseScraper

logger = structlog.get_logger()


class SerpAPIScraper(BaseScraper):
    """Google Jobs via SerpAPI."""

    @property
    def source_name(self) -> str:
        return "serpapi"

    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        if not self.settings.serpapi_api_key:
            logger.debug("serpapi_skipped", reason="no_api_key")
            return []

        params: dict[str, object] = {
            "engine": "google_jobs",
            "q": query,
            "api_key": self.settings.serpapi_api_key,
            "num": min(limit, 100),
        }
        if location:
            params["location"] = location

        resp = await self.client.get("https://serpapi.com/search", params=params)
        resp.raise_for_status()
        data = resp.json()

        jobs: list[ScrapedJob] = []
        for item in data.get("jobs_results", []):
            related = item.get("related_links") or [{}]
            extensions = item.get("detected_extensions", {})
            remote_raw = "remote" if extensions.get("work_from_home") else None
            sal_min, sal_max, sal_period = self._extract_salary(item.get("description", ""))

            jobs.append(
                ScrapedJob(
                    title=item.get("title", ""),
                    company_name=item.get("company_name", ""),
                    source=self.source_name,
                    source_url=related[0].get("link") if related[0] else None,
                    location=item.get("location", ""),
                    remote_type=self._normalize_remote_type(remote_raw),
                    description_raw=item.get("description", ""),
                    salary_min=sal_min,
                    salary_max=sal_max,
                    salary_period=sal_period,
                    posted_at=None,
                    extra_data={"extensions": extensions},
                )
            )
        return jobs[:limit]

    async def health_check(self) -> bool:
        if not self.settings.serpapi_api_key:
            return False
        try:
            resp = await self.client.get(
                "https://serpapi.com/account",
                params={"api_key": self.settings.serpapi_api_key},
            )
            return resp.status_code == 200
        except Exception:
            return False
