from __future__ import annotations

from datetime import datetime

import structlog

from app.scraping.port import ScrapedJob
from app.scraping.scrapers.base import BaseScraper

logger = structlog.get_logger()


class GreenhouseScraper(BaseScraper):
    """Greenhouse ATS job boards. Fetches from company boards."""

    @property
    def source_name(self) -> str:
        return "greenhouse"

    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        """Fetch from Greenhouse boards API. query = board token (company identifier)."""
        url = f"https://boards-api.greenhouse.io/v1/boards/{query}/jobs"
        params = {"content": "true"}

        resp = await self.client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            logger.warning("greenhouse.invalid_response_shape", query=query)
            return []
        jobs_data = data.get("jobs", [])
        if not isinstance(jobs_data, list):
            logger.warning("greenhouse.invalid_jobs_payload", query=query)
            return []

        jobs: list[ScrapedJob] = []
        for item in jobs_data:
            if not isinstance(item, dict):
                continue
            loc = item.get("location", {}).get("name", "")

            posted_at = None
            if item.get("updated_at"):
                try:
                    posted_at = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass

            # ATS ID: prefer internal_job_id, fallback to id
            raw_id = item.get("internal_job_id") or item.get("id")
            ats_job_id = str(raw_id) if raw_id is not None else None
            req_id = item.get("requisition_id")
            ats_req_id = str(req_id) if req_id else None

            jobs.append(
                ScrapedJob(
                    title=item.get("title", ""),
                    company_name=item.get("company", {}).get("name", query),
                    source=self.source_name,
                    source_url=item.get("absolute_url"),
                    location=loc,
                    remote_type=self._normalize_remote_type(loc),
                    description_raw=item.get("content", ""),
                    posted_at=posted_at,
                    ats_job_id=ats_job_id,
                    ats_requisition_id=ats_req_id,
                    ats_provider="greenhouse",
                )
            )
        return jobs[:limit]

    async def health_check(self) -> bool:
        try:
            resp = await self.client.get("https://boards-api.greenhouse.io/v1/boards/test/jobs")
            return resp.status_code in (200, 404)
        except Exception:
            return False
