from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ScrapedJob:
    """Normalized job from any scraper source."""

    title: str
    company_name: str
    source: str
    source_url: str | None = None
    location: str | None = None
    remote_type: str | None = None  # onsite, hybrid, remote
    description_raw: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_period: str | None = None  # annual, hourly, monthly
    salary_currency: str = "USD"
    experience_level: str | None = None
    job_type: str | None = None  # full-time, contract, part-time, internship
    posted_at: datetime | None = None
    company_domain: str | None = None
    company_logo_url: str | None = None
    ats_job_id: str | None = None
    ats_requisition_id: str | None = None
    ats_provider: str | None = None
    extra_data: dict = field(default_factory=dict)


class ScraperPort(ABC):
    """Abstract scraper interface. Python scrapers implement directly.
    Future Rust service implements via HTTP/gRPC adapter."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this source (e.g., 'serpapi', 'greenhouse')."""

    @abstractmethod
    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        """Fetch jobs matching query and location."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the scraper source is available."""

    async def close(self) -> None:
        """Cleanup resources. Override if needed."""
