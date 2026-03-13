"""Abstract base scraper with shared normalization utilities."""
from __future__ import annotations

import hashlib
import logging
import re
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

    # ------------------------------------------------------------------
    # Tech-stack detection
    # ------------------------------------------------------------------

    # Canonical tech terms used for detection.  The list is matched
    # case-insensitively but the canonical capitalisation is preserved in
    # the returned values.  Maximum 15 results are returned per call.
    TECH_TERMS: list[str] = [
        "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust",
        "Ruby", "PHP", "Swift", "Kotlin", "Scala", "C++", "C#",
        "React", "Angular", "Vue", "Next.js", "Node.js", "Django",
        "Flask", "FastAPI", "Spring", "Rails", "Laravel", "Express",
        "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "Kafka", "Spark", "Hadoop", "Airflow", "dbt",
    ]

    # Build a single regex that captures any of the terms.  Using word
    # boundaries prevents "Go" matching inside "MongoDB" etc.
    _TECH_PATTERN: re.Pattern = re.compile(
        r"\b(" + "|".join(re.escape(t) for t in TECH_TERMS) + r")\b",
        re.IGNORECASE,
    )
    # Map lower-cased term → canonical form for O(1) lookup
    _TECH_CANONICAL: dict[str, str] = {t.lower(): t for t in TECH_TERMS}

    # ------------------------------------------------------------------
    # Seniority inference
    # ------------------------------------------------------------------

    # Maps lower-cased token → output label.  Scanned left-to-right; the
    # first match wins.
    SENIORITY_MAP: dict[str, str] = {
        "intern": "intern",
        "internship": "intern",
        "junior": "entry",
        "entry": "entry",
        "entry-level": "entry",
        "associate": "entry",
        "mid": "mid",
        "mid-level": "mid",
        "senior": "senior",
        "sr": "senior",
        "sr.": "senior",
        "staff": "staff",
        "lead": "lead",
        "principal": "principal",
        "director": "director",
        "vp": "exec",
        "vice president": "exec",
        "cto": "exec",
        "ceo": "exec",
        "chief": "exec",
    }

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def fetch_jobs(
        self, query: str, location: str, limit: int = 100
    ) -> list[dict]:
        ...

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw: dict) -> dict:
        company = raw.get("company_name", "").strip()
        title = raw.get("title", "").strip()
        source = raw.get("source", self.source_name)

        description_raw = raw.get("description_raw") or raw.get("description", "")
        description_clean = self._clean_html(description_raw)
        description_markdown = self._html_to_markdown(description_raw)

        company_domain = raw.get("company_domain")
        if not company_domain and company:
            company_domain = (
                company.lower().replace(" ", "").replace(",", "") + ".com"
            )

        logo_url = raw.get("company_logo_url")
        if not logo_url and company_domain:
            logo_url = f"https://logo.clearbit.com/{company_domain}"

        # Dedup hash: stable across sources for the same company+title
        dedup_hash = self._compute_dedup_hash(company, title)

        # Tech stack from description if not supplied upstream
        tech_stack = raw.get("tech_stack") or self.extract_tech_stack(
            description_clean
        )

        # Experience level: prefer upstream value, else infer from title
        experience_level = raw.get("experience_level") or self._infer_seniority(title)

        # Salary normalisation
        salary_min, salary_max = self._normalize_salary(
            raw.get("salary_min"),
            raw.get("salary_max"),
            raw.get("salary_period", "year"),
        )

        return {
            "job_id": self.compute_job_id(source, company, title),
            "dedup_hash": dedup_hash,
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
            "experience_level": experience_level,
            "department": raw.get("department"),
            "industry": raw.get("industry"),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": raw.get("salary_currency", "USD"),
            "salary_period": raw.get("salary_period"),
            "description_raw": description_raw,
            "description_clean": description_clean,
            "description_markdown": description_markdown,
            "tech_stack": tech_stack,
            "status": "new",
            "is_starred": False,
            "is_enriched": False,
        }

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def compute_job_id(source: str, company: str, title: str) -> str:
        key = f"{source}:{company.lower().strip()}:{title.lower().strip()}"
        return hashlib.sha256(key.encode()).hexdigest()[:64]

    @staticmethod
    def _compute_dedup_hash(company: str, title: str) -> str:
        """Cross-source dedup hash: stable for same company+title pair."""
        key = f"{company.lower().strip()}:{title.lower().strip()}"
        return hashlib.sha256(key.encode()).hexdigest()[:32]

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

    @staticmethod
    def extract_tech_stack(description: str) -> list[str]:
        """Return up to 15 canonical tech terms found in *description*.

        Matching is case-insensitive; duplicates are removed while
        preserving first-seen order.
        """
        if not description:
            return []

        seen: set[str] = set()
        results: list[str] = []
        for match in BaseScraper._TECH_PATTERN.finditer(description):
            canonical = BaseScraper._TECH_CANONICAL[match.group(0).lower()]
            if canonical not in seen:
                seen.add(canonical)
                results.append(canonical)
                if len(results) == 15:
                    break

        return results

    @staticmethod
    def _infer_seniority(title: str) -> str | None:
        """Infer seniority level from job *title*.

        Returns one of: ``intern``, ``entry``, ``mid``, ``senior``,
        ``staff``, ``lead``, ``principal``, ``director``, ``exec``,
        or ``None`` when no signal is found.
        """
        if not title:
            return None

        lower = title.lower()

        # Check multi-word keys first (longest → shortest implicit via dict
        # ordering in Python 3.7+ — but we want explicit priority, so we
        # iterate SENIORITY_MAP which is ordered by insertion order above).
        for token, level in BaseScraper.SENIORITY_MAP.items():
            # Use word-boundary matching so "VP" doesn't match "MVP".
            pattern = r"\b" + re.escape(token) + r"\b"
            if re.search(pattern, lower):
                return level

        return None

    @staticmethod
    def _normalize_salary(
        min_val: float | None,
        max_val: float | None,
        interval: str | None,
    ) -> tuple[float | None, float | None]:
        """Convert salary values to an annual USD amount.

        Rules:
        - If both values are ``None``, return ``(None, None)``.
        - ``hourly`` → multiply by 2 080 (52 weeks × 40 h).
        - Suspiciously large annual values (> 1 000 000) are assumed to be
          in cents and divided by 100.
        """
        if min_val is None and max_val is None:
            return None, None

        period = (interval or "year").lower()

        def convert(v: float | None) -> float | None:
            if v is None:
                return None
            if "hour" in period:
                return v * 2080
            # Detect cent-denominated values (> $1 million raw)
            if v > 1_000_000:
                return v / 100
            return v

        return convert(min_val), convert(max_val)

    # ------------------------------------------------------------------
    # Location parsing
    # ------------------------------------------------------------------

    def _parse_location(self, location_str: str) -> dict:
        if not location_str:
            return {}
        parts = [p.strip() for p in location_str.split(",")]
        result: dict = {}
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

    # ------------------------------------------------------------------
    # Rate limiting (delegates to RateLimiter when available)
    # ------------------------------------------------------------------

    async def _rate_limit(self) -> None:
        """Honour per-source rate limits.

        Attempts to use the module-level :func:`get_limiter` so that the
        token bucket and circuit breaker are respected.  Falls back to a
        plain ``asyncio.sleep`` if the rate_limiter module is not
        importable (e.g., during isolated unit tests of a subclass).
        """
        try:
            from backend.scrapers.rate_limiter import get_limiter  # local import to avoid circular

            limiter = get_limiter(self.source_name or "generic")
            await limiter.acquire()
        except ImportError:
            import asyncio
            await asyncio.sleep(self.rate_limit_delay)
