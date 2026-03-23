from __future__ import annotations

import re

import httpx

from app.config import Settings
from app.scraping.port import ScrapedJob, ScraperPort


class BaseScraper(ScraperPort):
    """Base class for Python scrapers with shared functionality."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _normalize_remote_type(self, raw: str | None) -> str | None:
        """Normalize 'Work from home', 'WFH', 'Remote' → 'remote', etc."""
        if not raw:
            return None
        raw_lower = raw.lower()
        if any(kw in raw_lower for kw in ["remote", "wfh", "work from home", "anywhere"]):
            return "remote"
        if "hybrid" in raw_lower:
            return "hybrid"
        return "onsite"

    def _normalize_experience(self, raw: str | None) -> str | None:
        """Normalize experience level to: entry, mid, senior, lead, executive."""
        if not raw:
            return None
        raw_lower = raw.lower()
        if any(kw in raw_lower for kw in ["entry", "junior", "associate", "intern"]):
            return "entry"
        if any(kw in raw_lower for kw in ["mid", "intermediate"]):
            return "mid"
        if any(kw in raw_lower for kw in ["senior", "sr.", "sr "]):
            return "senior"
        if any(kw in raw_lower for kw in ["lead", "principal", "staff"]):
            return "lead"
        if any(kw in raw_lower for kw in ["director", "vp", "c-level", "executive", "chief"]):
            return "executive"
        return "mid"  # default

    def _extract_salary(self, text: str | None) -> tuple[float | None, float | None, str | None]:
        """Extract salary range from text using regex patterns."""
        if not text:
            return None, None, None

        # $120k-$150k or $120K-$150K
        m = re.search(r"\$(\d{2,4})[kK]\s*[-–to]+\s*\$?(\d{2,4})[kK]", text)
        if m:
            return float(m.group(1)) * 1000, float(m.group(2)) * 1000, "annual"

        # $120,000-$150,000 or $120000-$150000
        m = re.search(r"\$([\d,]+)\s*[-–to]+\s*\$?([\d,]+)", text)
        if m:
            lo = float(m.group(1).replace(",", ""))
            hi = float(m.group(2).replace(",", ""))
            if lo > 500:  # likely annual
                return lo, hi, "annual"
            return lo, hi, "hourly"

        # $50/hr or $50 per hour
        m = re.search(r"\$(\d+(?:\.\d+)?)\s*(?:/hr|per\s*hour)", text, re.IGNORECASE)
        if m:
            return float(m.group(1)), None, "hourly"

        return None, None, None

    def _make_scraped_job(self, **kwargs: object) -> ScrapedJob:
        """Helper to create ScrapedJob with source auto-set."""
        kwargs.setdefault("source", self.source_name)
        return ScrapedJob(**kwargs)  # type: ignore[arg-type]
