"""LLM-powered scraper that extracts structured job data from arbitrary HTML.

Uses an LLM (via OpenRouter) to parse job listings without hardcoded selectors.
Suitable for one-off career pages, niche ATS systems, or any URL that existing
scrapers cannot parse.
"""

from __future__ import annotations

import hashlib
import json
import re

import httpx
import structlog

from app.config import Settings
from app.enrichment.llm_client import LLMClient
from app.scraping.port import ScrapedJob, ScraperPort

logger = structlog.get_logger()

_HTML_TRUNCATE_CHARS = 8_000

_SYSTEM_PROMPT = """\
You are a precise HTML job-listing extractor. Given raw HTML from a careers or
job-board page, return ONLY a valid JSON array of job objects.

Each job object must have these keys (use null for any field you cannot find):
  - title       (string)  job title
  - company_name (string) hiring company
  - url         (string)  direct link to the job posting
  - location    (string)  city / state / country or "Remote"
  - remote_type (string)  one of: "remote", "hybrid", "onsite", "unknown"
  - job_type    (string)  one of: "full-time", "part-time", "contract",
                           "internship", or null
  - department  (string)  team or department if visible, else null
  - salary_min  (number)  minimum salary (annual USD), or null
  - salary_max  (number)  maximum salary (annual USD), or null
  - description (string)  job description text (plain text, no HTML tags)
  - posted_at   (string)  ISO-8601 date string if visible, else null

Rules:
- Return ONLY the JSON array, no markdown fences, no explanation.
- If no jobs are found, return an empty array: []
- Deduplicate identical postings.
- Strip all HTML tags from the description field.
"""


class AIScraper(ScraperPort):
    """Uses an LLM to parse arbitrary job pages without hardcoded selectors."""

    source_name = "ai_scraper"

    def __init__(self, settings: Settings, llm_client: LLMClient) -> None:
        self.settings = settings
        self._llm = llm_client
        self._http: httpx.AsyncClient | None = None
        self._content_cache: dict[str, list[ScrapedJob]] = {}

    @property
    def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        return self._http

    async def fetch_jobs(
        self, query: str, location: str | None = None, limit: int = 50
    ) -> list[ScrapedJob]:
        """Not used directly — use fetch_from_url for specific pages."""
        return []

    async def fetch_from_url(
        self, url: str, html: str | None = None, limit: int = 100
    ) -> list[ScrapedJob]:
        """Extract jobs from *url*, optionally using pre-fetched *html*."""
        if html is None:
            html = await self._fetch_html(url)
            if html is None:
                return []

        content_hash = hashlib.sha256(html.encode("utf-8", errors="replace")).hexdigest()[:32]
        if content_hash in self._content_cache:
            logger.info("ai_scraper.cache_hit", url=url, count=len(self._content_cache[content_hash]))
            return self._content_cache[content_hash][:limit]

        truncated = self._prepare_html(html)
        raw_jobs = await self._extract_with_llm(truncated, url)
        if raw_jobs is None:
            return []

        results: list[ScrapedJob] = []
        for raw in raw_jobs:
            if len(results) >= limit:
                break
            job = self._normalize_ai_job(raw, url)
            if job:
                results.append(job)

        self._content_cache[content_hash] = results
        logger.info("ai_scraper.extracted", url=url, count=len(results))
        return results

    async def health_check(self) -> bool:
        return self._llm.is_configured

    async def close(self) -> None:
        if self._http:
            await self._http.aclose()
            self._http = None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch_html(self, url: str) -> str | None:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; JobRadar/2.0)",
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        }
        try:
            resp = await self._client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPError as exc:
            logger.error("ai_scraper.fetch_failed", url=url, error=str(exc))
            return None

    @staticmethod
    def _prepare_html(html: str) -> str:
        for tag in ("script", "style", "noscript", "svg", "iframe"):
            html = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"[ \t]+", " ", html)
        html = re.sub(r"\n{3,}", "\n\n", html)
        return html[:_HTML_TRUNCATE_CHARS]

    async def _extract_with_llm(self, html: str, page_url: str) -> list[dict] | None:
        if not self._llm.is_configured:
            logger.warning("ai_scraper.llm_not_configured")
            return None

        try:
            raw = await self._llm.chat(
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": f"Page URL: {page_url}\n\nHTML:\n{html}"},
                ],
                temperature=0.0,
                max_tokens=4096,
            )
        except Exception as exc:
            logger.error("ai_scraper.llm_error", url=page_url, error=str(exc))
            return None

        return self._parse_llm_response(raw, page_url)

    @staticmethod
    def _parse_llm_response(raw_text: str, page_url: str) -> list[dict] | None:
        text = raw_text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1 or end <= start:
            logger.warning("ai_scraper.no_json_array", url=page_url)
            return None

        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            logger.warning("ai_scraper.json_parse_error", url=page_url)
            return None

        return data if isinstance(data, list) else None

    def _normalize_ai_job(self, raw: dict, page_url: str) -> ScrapedJob | None:
        title = (raw.get("title") or "").strip()
        if not title:
            return None

        remote = (raw.get("remote_type") or "").lower()
        if remote not in ("remote", "hybrid", "onsite"):
            remote = None

        salary_min = self._safe_float(raw.get("salary_min"))
        salary_max = self._safe_float(raw.get("salary_max"))

        return ScrapedJob(
            title=title,
            company_name=(raw.get("company_name") or "").strip(),
            source=self.source_name,
            source_url=(raw.get("url") or "").strip() or page_url,
            location=raw.get("location"),
            remote_type=remote,
            description_raw=(raw.get("description") or "").strip(),
            salary_min=salary_min,
            salary_max=salary_max,
            salary_period="annual" if (salary_min or salary_max) else None,
            job_type=raw.get("job_type"),
        )

    @staticmethod
    def _safe_float(value: object) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
