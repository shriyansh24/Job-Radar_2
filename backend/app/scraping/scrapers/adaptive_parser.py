"""Adaptive career page parser with fingerprint-based resilience.

Tries known CSS selectors for job listings, then falls back to heuristic
extraction. Designed to work with raw HTML strings (no Scrapling dependency).
"""

from __future__ import annotations

from urllib.parse import urljoin

import structlog
from bs4 import BeautifulSoup

logger = structlog.get_logger()

ADAPTIVE_SELECTORS = [
    ".job-listing", ".job-card", ".career-item", ".position-card",
    ".opening", "[data-job]", "[data-job-id]", ".jobs-list__item",
    ".job-post", "li.position",
    ".careers-list li", ".openings-list li", ".positions li",
    ".posting", ".job-board__item", ".careers-posting",
    "[data-posting-id]", ".lever-job", ".greenhouse-job",
]


class AdaptiveCareerParser:
    """Extract job listings from career page HTML using adaptive selectors."""

    def __init__(self, html: str, company_name: str = "", base_url: str = ""):
        self.html = html
        self.company_name = company_name
        self.base_url = base_url

    def extract(self) -> list[dict]:
        """Extract job listings: selector-first, then heuristic fallback."""
        soup = BeautifulSoup(self.html, "html.parser")

        results = self._extract_by_selectors(soup)
        if results:
            return results

        return self._extract_heuristic(soup)

    def _extract_by_selectors(self, soup: BeautifulSoup) -> list[dict]:
        listings: list[dict] = []

        for selector in ADAPTIVE_SELECTORS:
            elements = soup.select(selector)
            if not elements:
                continue

            for el in elements:
                listing = self._parse_element(el)
                if listing and listing.get("title"):
                    listings.append(listing)

            if listings:
                logger.debug(
                    "adaptive_parser.selector_match",
                    selector=selector,
                    count=len(listings),
                )
                break

        return listings

    def _parse_element(self, el) -> dict:
        link = el.select_one("a")
        heading = el.select_one("h1, h2, h3, h4, h5, h6")

        title = ""
        if heading:
            title = heading.get_text(strip=True)
        elif link:
            title = link.get_text(strip=True)

        url = ""
        if link and link.get("href"):
            url = urljoin(self.base_url, link["href"])

        location = ""
        for loc_cls in ("location", "place", "city", "loc"):
            loc_els = el.select(f"[class*='{loc_cls}']")
            if loc_els:
                location = loc_els[0].get_text(strip=True)
                break

        department = None
        for dept_cls in ("department", "team", "group", "dept"):
            dept_els = el.select(f"[class*='{dept_cls}']")
            if dept_els:
                department = dept_els[0].get_text(strip=True)
                break

        return {
            "title": title,
            "url": url,
            "company_name": self.company_name,
            "location": location,
            "department": department,
            "description_raw": "",
        }

    def _extract_heuristic(self, soup: BeautifulSoup) -> list[dict]:
        """Fallback: find all links that look like job postings."""
        listings: list[dict] = []
        job_keywords = ("job", "career", "position", "opening", "role", "apply")

        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            href_lower = href.lower()

            if any(kw in href_lower for kw in job_keywords) and len(text) > 5:
                listings.append({
                    "title": text,
                    "url": urljoin(self.base_url, href),
                    "company_name": self.company_name,
                    "location": "",
                    "description_raw": "",
                })

        return listings
