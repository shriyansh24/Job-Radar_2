"""ScrapingBee scraper — fetches JavaScript-rendered job listing pages.

Uses the ScrapingBee API to render JS-heavy career pages and job boards.
Requires JR_SCRAPINGBEE_API_KEY in settings; silently skipped when empty.
"""

from __future__ import annotations

import json
from datetime import datetime
from urllib.parse import quote_plus

import httpx
import structlog
from bs4 import BeautifulSoup

from app.config import Settings
from app.scraping.port import ScrapedJob, ScraperPort

logger = structlog.get_logger()


class ScrapingBeeScraper(ScraperPort):
    """Scraper using ScrapingBee API for JS-rendered pages."""

    source_name = "scrapingbee"
    BASE_URL = "https://app.scrapingbee.com/api/v1/"
    GOOGLE_JOBS_URL = "https://www.google.com/search?q={query}+jobs+{location}&ibp=htl;jobs"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        if not self.settings.scrapingbee_api_key:
            logger.warning("scrapingbee.not_configured")
            return []

        target_url = self.GOOGLE_JOBS_URL.format(
            query=quote_plus(query),
            location=quote_plus(location or ""),
        )

        params = {
            "api_key": self.settings.scrapingbee_api_key,
            "url": target_url,
            "render_js": "true",
            "premium_proxy": "true",
            "country_code": "us",
            "wait": "5000",
            "wait_for": "li",
            "block_ads": "true",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.get(self.BASE_URL, params=params)
                resp.raise_for_status()
                html = resp.text
            except httpx.HTTPError as e:
                logger.error("scrapingbee.request_failed", error=str(e))
                return []

        jobs = self._parse_google_jobs_html(html, location or "")
        logger.info("scrapingbee.fetched", query=query, location=location, count=len(jobs))
        return jobs[:limit]

    async def scrape_rendered_page(self, url: str) -> str | None:
        """Return the fully-rendered HTML of *url* via ScrapingBee."""
        if not self.settings.scrapingbee_api_key:
            return None

        params = {
            "api_key": self.settings.scrapingbee_api_key,
            "url": url,
            "render_js": "true",
            "premium_proxy": "true",
            "block_ads": "true",
            "wait": "3000",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.get(self.BASE_URL, params=params)
                resp.raise_for_status()
                return resp.text
            except httpx.HTTPError as e:
                logger.error("scrapingbee.render_failed", url=url, error=str(e))
                return None

    async def health_check(self) -> bool:
        return bool(self.settings.scrapingbee_api_key)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_google_jobs_html(self, html: str, location: str) -> list[ScrapedJob]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[ScrapedJob] = []

        for script_tag in soup.find_all("script", {"type": "application/ld+json"}):
            try:
                data = json.loads(script_tag.string or "")
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict):
                        if item.get("@type") == "JobPosting":
                            job = self._normalize_ld_json(item, location)
                            if job:
                                jobs.append(job)
                        for sub in item.get("itemListElement", []):
                            if isinstance(sub, dict):
                                job = self._normalize_ld_json(sub, location)
                                if job:
                                    jobs.append(job)
            except (json.JSONDecodeError, TypeError):
                continue

        if not jobs:
            jobs = self._parse_job_cards(soup, location)

        return jobs

    def _parse_job_cards(self, soup: BeautifulSoup, location: str) -> list[ScrapedJob]:
        jobs: list[ScrapedJob] = []
        for card in soup.select("[data-hveid] li, .iFjolb, .PwjeAc"):
            title_el = card.select_one(".BjJfJf, .sH3zFd, [role='heading']")
            company_el = card.select_one(".vNEEBe, .nJlDiv")
            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else ""
            if not title or not company:
                continue

            link_el = card.select_one("a[href]")
            url = link_el["href"] if link_el else ""
            desc_el = card.select_one(".HBvzbc, .YgLbBe")
            description = desc_el.get_text(strip=True) if desc_el else ""

            jobs.append(ScrapedJob(
                title=title,
                company_name=company,
                source=self.source_name,
                source_url=url,
                location=location,
                description_raw=description,
            ))
        return jobs

    def _normalize_ld_json(self, data: dict, fallback_location: str) -> ScrapedJob | None:
        if not isinstance(data, dict) or data.get("@type") not in ("JobPosting", None):
            return None

        title = (data.get("title") or "").strip()
        if not title:
            return None

        hiring_org = data.get("hiringOrganization", {})
        company = hiring_org.get("name", "").strip() if isinstance(hiring_org, dict) else str(hiring_org).strip()
        if not company:
            return None

        # Location
        location_str = fallback_location
        job_location = data.get("jobLocation", {})
        if isinstance(job_location, dict):
            address = job_location.get("address", {})
            if isinstance(address, dict):
                parts = [address.get("addressLocality", ""), address.get("addressRegion", "")]
                location_str = ", ".join(p for p in parts if p) or fallback_location

        # Remote
        remote_type = None
        jlt = data.get("jobLocationType", "")
        if isinstance(jlt, str) and "remote" in jlt.lower():
            remote_type = "remote"

        # Salary
        salary_min = salary_max = None
        salary_period = None
        salary_spec = data.get("baseSalary", {})
        if isinstance(salary_spec, dict):
            value = salary_spec.get("value", {})
            if isinstance(value, dict):
                salary_min = value.get("minValue")
                salary_max = value.get("maxValue")
                if salary_min:
                    salary_min = float(salary_min)
                if salary_max:
                    salary_max = float(salary_max)
                unit = str(salary_spec.get("unitText", "")).lower()
                salary_period = "hourly" if "hour" in unit else "annual"

        # Posted
        posted_at = None
        dp = data.get("datePosted")
        if dp:
            try:
                posted_at = datetime.fromisoformat(str(dp).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        return ScrapedJob(
            title=title,
            company_name=company,
            source=self.source_name,
            source_url=data.get("url", ""),
            location=location_str,
            remote_type=remote_type,
            description_raw=data.get("description", ""),
            salary_min=salary_min,
            salary_max=salary_max,
            salary_period=salary_period,
            posted_at=posted_at,
        )
