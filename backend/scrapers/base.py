import hashlib
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

import html2text
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

h2t = html2text.HTML2Text()
h2t.ignore_links = False
h2t.ignore_images = True
h2t.body_width = 0


class BaseScraper(ABC):
    source_name: str = ""
    rate_limit_delay: float = 1.0

    @abstractmethod
    async def fetch_jobs(
        self, query: str, location: str, limit: int = 100
    ) -> list[dict]:
        ...

    def normalize(self, raw: dict) -> dict:
        company = raw.get("company_name", "").strip()
        title = raw.get("title", "").strip()
        source = raw.get("source", self.source_name)

        description_raw = raw.get("description_raw") or raw.get("description", "")
        description_clean = self._clean_html(description_raw)
        description_markdown = self._html_to_markdown(description_raw)

        company_domain = raw.get("company_domain")
        if not company_domain and company:
            company_domain = company.lower().replace(" ", "").replace(",", "") + ".com"

        logo_url = raw.get("company_logo_url")
        if not logo_url and company_domain:
            logo_url = f"https://logo.clearbit.com/{company_domain}"

        return {
            "job_id": self.compute_job_id(source, company, title),
            "source": source,
            "url": raw.get("url", ""),
            "posted_at": raw.get("posted_at"),
            "scraped_at": datetime.utcnow(),
            "is_active": True,
            "company_name": company,
            "company_domain": company_domain,
            "company_logo_url": logo_url,
            "title": title,
            "location_city": raw.get("location_city"),
            "location_state": raw.get("location_state"),
            "location_country": raw.get("location_country", "US"),
            "remote_type": raw.get("remote_type", "unknown"),
            "job_type": raw.get("job_type"),
            "experience_level": raw.get("experience_level"),
            "department": raw.get("department"),
            "industry": raw.get("industry"),
            "salary_min": raw.get("salary_min"),
            "salary_max": raw.get("salary_max"),
            "salary_currency": raw.get("salary_currency", "USD"),
            "salary_period": raw.get("salary_period"),
            "description_raw": description_raw,
            "description_clean": description_clean,
            "description_markdown": description_markdown,
            "status": "new",
            "is_starred": False,
            "is_enriched": False,
        }

    @staticmethod
    def compute_job_id(source: str, company: str, title: str) -> str:
        key = f"{source}:{company.lower().strip()}:{title.lower().strip()}"
        return hashlib.sha256(key.encode()).hexdigest()[:64]

    @staticmethod
    def _clean_html(html: str) -> str:
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator=" ", strip=True)

    @staticmethod
    def _html_to_markdown(html: str) -> str:
        if not html:
            return ""
        return h2t.handle(html).strip()

    def _parse_location(self, location_str: str) -> dict:
        if not location_str:
            return {}
        parts = [p.strip() for p in location_str.split(",")]
        result = {}
        if len(parts) >= 1:
            result["location_city"] = parts[0]
        if len(parts) >= 2:
            result["location_state"] = parts[1]
        if len(parts) >= 3:
            result["location_country"] = parts[2]

        lower = location_str.lower()
        if "remote" in lower:
            result["remote_type"] = "remote"
        elif "hybrid" in lower:
            result["remote_type"] = "hybrid"
        else:
            result["remote_type"] = "onsite"

        return result

    async def _rate_limit(self):
        await asyncio.sleep(self.rate_limit_delay)
