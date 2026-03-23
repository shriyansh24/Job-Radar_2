"""Workday ATS scraper — fetches jobs from Workday career sites.

Workday uses a JSON API at:
    POST https://{tenant}.{subdomain}.myworkdayjobs.com/wday/cxs/{tenant}/{section}/jobs

URL format:
    https://{tenant}.{subdomain}.myworkdayjobs.com/{locale}/{section}
    e.g. https://microsoft.wd5.myworkdayjobs.com/en-US/Global
"""

from __future__ import annotations

import re
from datetime import datetime

import structlog

from app.scraping.port import ScrapedJob
from app.scraping.scrapers.base import BaseScraper

logger = structlog.get_logger()

# Matches: https://{tenant}.{subdomain}.myworkdayjobs.com[/{locale}]/{section}[/...]
_WORKDAY_URL_RE = re.compile(
    r"https?://(?P<tenant>[^.]+)\.(?P<subdomain>wd\d+)\.myworkdayjobs\.com"
    r"(?:/[a-z]{2}-[A-Z]{2,3})?"  # optional locale like /en-US
    r"/(?P<section>[^/?#]+)",
    re.IGNORECASE,
)


class WorkdayScraper(BaseScraper):
    """Scraper for Workday ATS career pages."""

    @property
    def source_name(self) -> str:
        return "workday"

    def _extract_tenant(self, url: str) -> tuple[str, str, str]:
        """Extract (tenant, subdomain, section) from a Workday URL.

        Args:
            url: Full Workday career page URL.

        Returns:
            Tuple of (tenant, subdomain, career_section).

        Raises:
            ValueError: If the URL doesn't match Workday pattern.
        """
        m = _WORKDAY_URL_RE.match(url)
        if not m:
            raise ValueError(f"Not a valid Workday URL: {url}")
        return m.group("tenant"), m.group("subdomain"), m.group("section")

    def _build_api_url(self, tenant: str, subdomain: str, section: str) -> str:
        """Build the Workday jobs API endpoint URL."""
        return f"https://{tenant}.{subdomain}.myworkdayjobs.com/wday/cxs/{tenant}/{section}/jobs"

    def _build_payload(
        self,
        limit: int = 20,
        offset: int = 0,
        query: str | None = None,
        location: str | None = None,
    ) -> dict:
        """Build the JSON payload for the Workday jobs API POST request."""
        payload: dict = {
            "limit": limit,
            "offset": offset,
            "appliedFacets": {},
        }
        if query:
            payload["searchText"] = query
        if location:
            payload["locations"] = [{"value": location}]
        return payload

    def _parse_response(self, data: dict, base_url: str) -> list[ScrapedJob]:
        """Parse Workday API JSON response into ScrapedJob objects.

        Args:
            data: Raw JSON response from Workday API.
            base_url: The base URL of the Workday site for building job URLs.

        Returns:
            List of ScrapedJob objects.
        """
        # Extract tenant from the base URL for company name
        m = re.match(r"https?://([^.]+)\.", base_url)
        company = m.group(1) if m else "unknown"

        jobs: list[ScrapedJob] = []
        for posting in data.get("jobPostings", []):
            title = posting.get("title", "")
            location = posting.get("locationsText")
            external_path = posting.get("externalPath", "")
            bullet_fields = posting.get("bulletFields", [])

            # Build full URL
            source_url = f"{base_url}{external_path}" if external_path else None

            # Parse posted date
            posted_at = None
            posted_on = posting.get("postedOn")
            if posted_on:
                try:
                    posted_at = datetime.fromisoformat(posted_on)
                except (ValueError, TypeError):
                    pass

            # Extract job type from bullet fields (e.g. "Full-time", "Contract")
            job_type = bullet_fields[0] if bullet_fields else None

            # Determine remote type
            remote_type = self._normalize_remote_type(location)

            # ATS ID: try REQ-\d+ from externalPath, fallback to trailing path segment
            req_match = re.search(r"(REQ-\d+)", external_path)
            if req_match:
                ats_job_id = req_match.group(1)
            else:
                # Fallback: last path segment (e.g. /job/Title/12345 -> 12345)
                path_parts = external_path.rstrip("/").split("/")
                ats_job_id = path_parts[-1] if path_parts else None

            jobs.append(
                ScrapedJob(
                    title=title,
                    company_name=company,
                    source=self.source_name,
                    source_url=source_url,
                    location=location,
                    remote_type=remote_type,
                    job_type=job_type,
                    posted_at=posted_at,
                    ats_job_id=ats_job_id,
                    ats_provider="workday",
                )
            )

        return jobs

    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        """Fetch jobs from a Workday career page.

        Args:
            query: Workday career page URL (e.g.
                   "https://microsoft.wd5.myworkdayjobs.com/en-US/Global")
                   OR a search query if a default URL has been configured.
            location: Optional location filter.
            limit: Maximum number of jobs to return.

        Returns:
            List of ScrapedJob objects.
        """
        tenant, subdomain, section = self._extract_tenant(query)
        api_url = self._build_api_url(tenant, subdomain, section)
        base_url = f"https://{tenant}.{subdomain}.myworkdayjobs.com"

        payload = self._build_payload(limit=limit, offset=0, location=location)

        logger.info(
            "workday.fetch_jobs",
            tenant=tenant,
            section=section,
            api_url=api_url,
        )

        resp = await self.client.post(
            api_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            logger.warning("workday.invalid_response_shape", url=query)
            return []
        if not isinstance(data.get("jobPostings", []), list):
            logger.warning("workday.invalid_job_postings", url=query)
            return []

        jobs = self._parse_response(data, base_url)
        logger.info("workday.fetched", count=len(jobs), total=data.get("total"))
        return jobs[:limit]

    async def health_check(self) -> bool:
        """Check connectivity to a known Workday endpoint."""
        try:
            # Use a known public Workday endpoint to verify reachability
            resp = await self.client.get(
                "https://microsoft.wd5.myworkdayjobs.com",
                follow_redirects=True,
            )
            return resp.status_code < 500
        except Exception:
            return False
