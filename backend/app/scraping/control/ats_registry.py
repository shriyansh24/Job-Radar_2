"""Data-driven ATS classification registry."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ATSClassification:
    vendor: str | None
    board_token: str | None
    start_tier: int


ATS_RULES: list[dict] = [
    {
        "vendor": "greenhouse",
        "url_patterns": ["boards.greenhouse.io/", ".greenhouse.io/"],
        "header_signatures": ["X-Greenhouse"],
        "html_signatures": ['content="Greenhouse"'],
        "start_tier": 0,
        "token_pattern": r"greenhouse\.io/([^/?#]+)",
    },
    {
        "vendor": "lever",
        "url_patterns": ["jobs.lever.co/"],
        "header_signatures": ["X-Powered-By: Lever"],
        "html_signatures": ["lever-jobs-container"],
        "start_tier": 0,
        "token_pattern": r"lever\.co/([^/?#]+)",
    },
    {
        "vendor": "ashby",
        "url_patterns": ["jobs.ashbyhq.com/"],
        "header_signatures": [],
        "html_signatures": ["ashby-job-posting"],
        "start_tier": 0,
        "token_pattern": r"ashbyhq\.com/([^/?#]+)",
    },
    {
        "vendor": "workday",
        "url_patterns": [".myworkdayjobs.com"],
        "header_signatures": [],
        "html_signatures": ["wday/cxs"],
        "start_tier": 0,
        "token_pattern": r"([\w-]+)\.(?:wd\d\.)?myworkdayjobs\.com",
    },
    {
        "vendor": "icims",
        "url_patterns": [".icims.com"],
        "header_signatures": [],
        "html_signatures": [],
        "start_tier": 1,
        "token_pattern": None,
    },
    {
        "vendor": "smartrecruiters",
        "url_patterns": [".smartrecruiters.com"],
        "header_signatures": [],
        "html_signatures": [],
        "start_tier": 1,
        "token_pattern": None,
    },
    {
        "vendor": "jobvite",
        "url_patterns": [".jobvite.com"],
        "header_signatures": [],
        "html_signatures": [],
        "start_tier": 1,
        "token_pattern": None,
    },
    {
        "vendor": "breezy",
        "url_patterns": [".breezy.hr"],
        "header_signatures": [],
        "html_signatures": [],
        "start_tier": 1,
        "token_pattern": None,
    },
]


def classify_url(url: str) -> ATSClassification:
    """Classify a URL by walking the ATS registry."""
    url_lower = url.lower()
    for rule in ATS_RULES:
        for pattern in rule["url_patterns"]:
            if pattern.lower() in url_lower:
                token = _extract_token(url, rule.get("token_pattern"))
                return ATSClassification(
                    vendor=rule["vendor"],
                    board_token=token,
                    start_tier=rule["start_tier"],
                )
    return ATSClassification(vendor=None, board_token=None, start_tier=1)


def classify_headers(headers: dict[str, str]) -> ATSClassification | None:
    """Classify from HTTP response headers."""
    header_str = str(headers).lower()
    for rule in ATS_RULES:
        for sig in rule.get("header_signatures", []):
            if sig.lower() in header_str:
                return ATSClassification(
                    vendor=rule["vendor"], board_token=None, start_tier=rule["start_tier"]
                )
    return None


def classify_html(html: str) -> ATSClassification | None:
    """Classify from HTML content (first 5KB)."""
    snippet = html[:5120].lower()
    for rule in ATS_RULES:
        for sig in rule.get("html_signatures", []):
            if sig.lower() in snippet:
                return ATSClassification(
                    vendor=rule["vendor"], board_token=None, start_tier=rule["start_tier"]
                )
    return None


def _extract_token(url: str, pattern: str | None) -> str | None:
    if not pattern:
        return None
    match = re.search(pattern, url, re.IGNORECASE)
    return match.group(1) if match else None
