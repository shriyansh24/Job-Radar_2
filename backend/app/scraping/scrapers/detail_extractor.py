"""Extract rich job details from individual job posting pages.

Uses BeautifulSoup for deep DOM traversal — extracts description, salary,
requirements, benefits, and posted date from JSON-LD or HTML heuristics.
"""

from __future__ import annotations

import json
import re

import structlog
from bs4 import BeautifulSoup

logger = structlog.get_logger()


class DetailPageExtractor:
    """Extract full job details from an individual job posting page.

    Priority: JSON-LD JobPosting schema > HTML heuristic extraction.
    """

    SALARY_PATTERNS = [
        re.compile(r"\$(\d{2,3})[kK]\s*[-\u2013\u2014to]+\s*\$(\d{2,3})[kK]"),
        re.compile(r"\$([\d,]+)\s*[-\u2013\u2014to]+\s*\$([\d,]+)"),
        re.compile(r"\$(\d+)\s*/\s*(?:hr|hour)\s*[-\u2013\u2014to]+\s*\$(\d+)\s*/\s*(?:hr|hour)", re.I),
    ]

    @classmethod
    def extract(cls, html: str) -> dict:
        """Extract detail data from job posting HTML.

        Returns dict with: description_raw, salary_min, salary_max,
        salary_period, requirements, benefits, posted_at.
        """
        soup = BeautifulSoup(html, "html.parser")

        detail = cls._extract_json_ld(soup)
        if detail.get("description_raw"):
            return detail

        return cls._extract_heuristic(soup)

    @classmethod
    def _extract_json_ld(cls, soup: BeautifulSoup) -> dict:
        result: dict = {}
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue

            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict) or item.get("@type") != "JobPosting":
                    continue

                result["description_raw"] = item.get("description", "")

                salary = item.get("baseSalary", {})
                if isinstance(salary, dict):
                    value = salary.get("value", {})
                    if isinstance(value, dict):
                        result["salary_min"] = value.get("minValue")
                        result["salary_max"] = value.get("maxValue")
                        unit = salary.get("unitText", "YEAR")
                        result["salary_period"] = "hour" if "HOUR" in unit.upper() else "year"

                result["posted_at"] = item.get("datePosted")

                quals = item.get("qualifications") or item.get("experienceRequirements")
                if isinstance(quals, str):
                    result["requirements"] = [quals]
                elif isinstance(quals, list):
                    result["requirements"] = quals

                break

        return result

    @classmethod
    def _extract_heuristic(cls, soup: BeautifulSoup) -> dict:
        result: dict = {}

        desc_selectors = [
            ".job-description", ".description", ".posting-description",
            "#job-description", "[data-qa='job-description']",
            "article", ".content-body", ".job-details",
        ]
        for sel in desc_selectors:
            el = soup.select_one(sel)
            if el:
                result["description_raw"] = str(el)
                break

        page_text = soup.get_text(separator=" ", strip=True)
        for pattern in cls.SALARY_PATTERNS:
            match = pattern.search(page_text)
            if match:
                groups = match.groups()
                min_val = cls._parse_salary_value(groups[0])
                max_val = cls._parse_salary_value(groups[1]) if len(groups) > 1 else None
                if min_val:
                    result["salary_min"] = min_val
                if max_val:
                    result["salary_max"] = max_val
                if "/hr" in match.group(0).lower() or "/hour" in match.group(0).lower():
                    result["salary_period"] = "hour"
                elif "k" in match.group(0).lower():
                    result["salary_period"] = "year"
                    if result.get("salary_min"):
                        result["salary_min"] *= 1000
                    if result.get("salary_max"):
                        result["salary_max"] *= 1000
                break

        for heading in soup.find_all(re.compile(r"^h[2-4]$")):
            if re.search(r"require|qualif|must.have|what.you.need", heading.get_text(), re.I):
                ul = heading.find_next("ul")
                if ul:
                    result["requirements"] = [li.get_text(strip=True) for li in ul.find_all("li")]
                break

        for heading in soup.find_all(re.compile(r"^h[2-4]$")):
            if re.search(r"benefit|perk|what.we.offer|compensation", heading.get_text(), re.I):
                ul = heading.find_next("ul")
                if ul:
                    result["benefits"] = [li.get_text(strip=True) for li in ul.find_all("li")]
                break

        return result

    @staticmethod
    def _parse_salary_value(raw: str) -> float | None:
        try:
            return float(raw.replace(",", ""))
        except (ValueError, TypeError):
            return None
