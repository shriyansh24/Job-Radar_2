from __future__ import annotations

import asyncio

import structlog

from app.scraping.port import ScrapedJob
from app.scraping.scrapers.base import BaseScraper

logger = structlog.get_logger()


class JobSpyScraper(BaseScraper):
    """Uses python-jobspy library to scrape Indeed, LinkedIn, ZipRecruiter, Glassdoor."""

    @property
    def source_name(self) -> str:
        return "jobspy"

    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        """Use jobspy in a thread executor since it's synchronous."""
        try:
            from jobspy import scrape_jobs
        except ImportError:
            logger.warning("jobspy_not_installed", hint="pip install python-jobspy")
            return []

        loop = asyncio.get_event_loop()
        try:
            df = await loop.run_in_executor(
                None,
                lambda: scrape_jobs(
                    site_name=["indeed", "linkedin", "zip_recruiter", "glassdoor"],
                    search_term=query,
                    location=location or "United States",
                    results_wanted=limit,
                    hours_old=72,
                    country_indeed="USA",
                ),
            )
        except Exception as e:
            logger.error("jobspy_scrape_failed", error=str(e))
            return []

        jobs: list[ScrapedJob] = []
        for _, row in df.iterrows():
            sal_min, sal_max, sal_period = None, None, None
            if row.get("min_amount"):
                sal_min = float(row["min_amount"])
            if row.get("max_amount"):
                sal_max = float(row["max_amount"])
            if row.get("interval"):
                sal_period = str(row["interval"]).lower()

            jobs.append(
                ScrapedJob(
                    title=str(row.get("title", "")),
                    company_name=str(row.get("company", "")),
                    source=f"jobspy_{row.get('site', 'unknown')}",
                    source_url=str(row.get("job_url", "")),
                    location=str(row.get("location", "")),
                    remote_type=self._normalize_remote_type(str(row.get("is_remote", ""))),
                    description_raw=str(row.get("description", "")),
                    salary_min=sal_min,
                    salary_max=sal_max,
                    salary_period=sal_period,
                    job_type=str(row.get("job_type", "")),
                )
            )
        return jobs[:limit]

    async def health_check(self) -> bool:
        try:
            from jobspy import scrape_jobs  # noqa: F401

            return True
        except ImportError:
            return False
