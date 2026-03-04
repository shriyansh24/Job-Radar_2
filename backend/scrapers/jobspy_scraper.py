import asyncio
import logging
from datetime import datetime
from typing import Optional

from backend.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class JobSpyScraper(BaseScraper):
    source_name = "jobspy"
    rate_limit_delay = 2.0

    async def fetch_jobs(
        self, query: str, location: str, limit: int = 100
    ) -> list[dict]:
        try:
            from jobspy import scrape_jobs
        except ImportError:
            logger.error("python-jobspy not installed")
            return []

        loop = asyncio.get_event_loop()
        try:
            df = await loop.run_in_executor(
                None,
                lambda: scrape_jobs(
                    site_name=["linkedin", "indeed", "glassdoor", "google", "zip_recruiter"],
                    search_term=query,
                    location=location,
                    results_wanted=limit,
                    hours_old=72,
                    country_indeed="USA",
                ),
            )
        except Exception as e:
            logger.error(f"JobSpy scrape failed: {e}")
            return []

        if df is None or df.empty:
            logger.info("JobSpy: no results returned")
            return []

        records = df.to_dict("records")
        all_jobs = []
        for record in records:
            normalized = self._normalize_jobspy(record)
            if normalized:
                all_jobs.append(normalized)

        logger.info(f"JobSpy: fetched {len(all_jobs)} jobs for '{query}' in '{location}'")
        return all_jobs[:limit]

    def _normalize_jobspy(self, raw: dict) -> Optional[dict]:
        title = str(raw.get("title", "")).strip()
        company = str(raw.get("company_name", raw.get("company", ""))).strip()
        if not title or not company or title == "nan" or company == "nan":
            return None

        location_str = str(raw.get("location", ""))
        location_parts = self._parse_location(location_str)

        # Parse salary
        salary_min = raw.get("min_amount")
        salary_max = raw.get("max_amount")
        salary_period = raw.get("interval")
        if salary_min and str(salary_min) == "nan":
            salary_min = None
        if salary_max and str(salary_max) == "nan":
            salary_max = None
        if salary_period and str(salary_period) == "nan":
            salary_period = None

        # Parse job type
        job_type_raw = str(raw.get("job_type", ""))
        job_type = None
        if job_type_raw and job_type_raw != "nan":
            lower = job_type_raw.lower()
            if "full" in lower:
                job_type = "full-time"
            elif "part" in lower:
                job_type = "part-time"
            elif "contract" in lower:
                job_type = "contract"
            elif "intern" in lower:
                job_type = "internship"

        description = str(raw.get("description", ""))
        if description == "nan":
            description = ""

        url = str(raw.get("job_url", raw.get("link", "")))
        if url == "nan":
            url = ""

        date_posted = raw.get("date_posted")
        posted_at = None
        if date_posted and str(date_posted) != "nan" and str(date_posted) != "NaT":
            try:
                if hasattr(date_posted, "to_pydatetime"):
                    posted_at = date_posted.to_pydatetime()
                elif isinstance(date_posted, str):
                    posted_at = datetime.fromisoformat(date_posted)
            except (ValueError, TypeError):
                pass

        is_remote = raw.get("is_remote")
        remote_type = location_parts.get("remote_type", "unknown")
        if is_remote is True:
            remote_type = "remote"

        site = str(raw.get("site", ""))
        company_domain = raw.get("company_url")
        if company_domain and str(company_domain) != "nan":
            company_domain = str(company_domain).replace("https://", "").replace("http://", "").rstrip("/")
        else:
            company_domain = None

        job_data = {
            "title": title,
            "company_name": company,
            "company_domain": company_domain,
            "url": url,
            "description_raw": description,
            "description": description,
            "source": self.source_name,
            "posted_at": posted_at,
            "job_type": job_type,
            "salary_min": float(salary_min) if salary_min else None,
            "salary_max": float(salary_max) if salary_max else None,
            "salary_period": str(salary_period) if salary_period else None,
            "remote_type": remote_type,
            **{k: v for k, v in location_parts.items() if k != "remote_type"},
        }

        return self.normalize(job_data)
