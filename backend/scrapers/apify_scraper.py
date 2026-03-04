import logging
from datetime import datetime
from typing import Optional

import httpx

from backend.config import get_settings
from backend.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class ApifyScraper(BaseScraper):
    source_name = "apify"
    rate_limit_delay = 1.0

    BASE_URL = "https://api.apify.com/v2"

    def __init__(self):
        self.settings = get_settings()

    async def fetch_jobs(
        self,
        query: str,
        location: str,
        limit: int = 100,
        actor_id: str = "hMvNSpz3JnHgl5jkh",
    ) -> list[dict]:
        if not self.settings.APIFY_KEY:
            logger.warning("Apify key not configured, skipping")
            return []

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Start actor run
            run_url = f"{self.BASE_URL}/acts/{actor_id}/runs"
            headers = {"Authorization": f"Bearer {self.settings.APIFY_KEY}"}
            run_input = {
                "queries": [query],
                "location": location,
                "maxResults": limit,
            }

            try:
                resp = await client.post(
                    run_url, json=run_input, headers=headers
                )
                resp.raise_for_status()
                run_data = resp.json()
            except httpx.HTTPError as e:
                logger.error(f"Apify actor start failed: {e}")
                return []

            run_id = run_data.get("data", {}).get("id")
            if not run_id:
                logger.error("Apify: no run ID returned")
                return []

            # Wait for completion
            import asyncio
            dataset_id = None
            for _ in range(60):
                await asyncio.sleep(2)
                try:
                    status_resp = await client.get(
                        f"{self.BASE_URL}/actor-runs/{run_id}",
                        headers=headers,
                    )
                    status_data = status_resp.json().get("data", {})
                    status = status_data.get("status")
                    if status == "SUCCEEDED":
                        dataset_id = status_data.get("defaultDatasetId")
                        break
                    elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                        logger.error(f"Apify run {status}")
                        return []
                except httpx.HTTPError:
                    continue

            if not dataset_id:
                logger.error("Apify: run did not complete in time")
                return []

            # Fetch results
            try:
                items_resp = await client.get(
                    f"{self.BASE_URL}/datasets/{dataset_id}/items",
                    headers=headers,
                    params={"limit": limit},
                )
                items_resp.raise_for_status()
                items = items_resp.json()
            except httpx.HTTPError as e:
                logger.error(f"Apify dataset fetch failed: {e}")
                return []

        all_jobs = []
        for item in items:
            normalized = self._normalize_apify(item)
            if normalized:
                all_jobs.append(normalized)

        logger.info(f"Apify: fetched {len(all_jobs)} jobs")
        return all_jobs[:limit]

    def _normalize_apify(self, raw: dict) -> Optional[dict]:
        title = raw.get("title", raw.get("positionName", "")).strip()
        company = raw.get("company", raw.get("companyName", "")).strip()
        if not title or not company:
            return None

        location_str = raw.get("location", "")
        location_parts = self._parse_location(location_str)

        posted_at = None
        date_str = raw.get("postedAt", raw.get("scrapedAt"))
        if date_str:
            try:
                posted_at = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        job_data = {
            "title": title,
            "company_name": company,
            "url": raw.get("url", raw.get("jobUrl", "")),
            "description_raw": raw.get("descriptionHtml", raw.get("description", "")),
            "description": raw.get("description", raw.get("descriptionHtml", "")),
            "source": self.source_name,
            "posted_at": posted_at,
            **location_parts,
        }

        return self.normalize(job_data)
