"""ATS URL pattern detection for 15 providers.

Detects which Applicant Tracking System a job posting URL belongs to,
extracts company slugs, and builds canonical API URLs for supported providers.
"""
from __future__ import annotations

import re
from typing import Optional

# ---------------------------------------------------------------------------
# ATS URL patterns
# Each entry: (provider_name, compiled_regex)
# Patterns are evaluated in order; first match wins.
# ---------------------------------------------------------------------------

_ATS_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("greenhouse",      re.compile(r"boards\.greenhouse\.io", re.IGNORECASE)),
    ("lever",           re.compile(r"jobs\.lever\.co", re.IGNORECASE)),
    ("ashby",           re.compile(r"jobs\.ashbyhq\.com", re.IGNORECASE)),
    ("workday",         re.compile(r"myworkdayjobs\.com", re.IGNORECASE)),
    ("linkedin",        re.compile(r"linkedin\.com/jobs", re.IGNORECASE)),
    ("indeed",          re.compile(r"indeed\.com/(viewjob|rc/clk|job/)", re.IGNORECASE)),
    ("icims",           re.compile(r"jobs\.icims\.com|\.icims\.com/jobs", re.IGNORECASE)),
    ("taleo",           re.compile(r"taleo\.net/(careersection|servlet)", re.IGNORECASE)),
    ("smartrecruiters", re.compile(r"jobs\.smartrecruiters\.com|smartrecruiters\.com/jobs", re.IGNORECASE)),
    ("jobvite",         re.compile(r"jobs\.jobvite\.com|jobvite\.com/careers", re.IGNORECASE)),
    ("breezyhr",        re.compile(r"breezy\.hr|\.breezy\.hr", re.IGNORECASE)),
    ("jazz",            re.compile(r"app\.jazz\.co|\.jazz\.co/apply", re.IGNORECASE)),
    ("ultipro",         re.compile(r"ultipro\.com/.*careers|e\d+\.ultipro\.com", re.IGNORECASE)),
    ("dayforce",        re.compile(r"dayforcehcm\.com|dayforce\.com.*careers", re.IGNORECASE)),
    ("bamboohr",        re.compile(r"\.bamboohr\.com/jobs|bamboohr\.com/careers", re.IGNORECASE)),
]

# ---------------------------------------------------------------------------
# Slug extraction patterns — keyed by provider
# Each regex must have a named group "slug" (or group 1) capturing the slug.
# ---------------------------------------------------------------------------

_SLUG_PATTERNS: dict[str, re.Pattern] = {
    # https://boards.greenhouse.io/{slug}/jobs/...  or  /jobs/{slug}/...
    "greenhouse": re.compile(
        r"boards\.greenhouse\.io/([^/?#]+)", re.IGNORECASE
    ),
    # https://jobs.lever.co/{slug}[/...]
    "lever": re.compile(
        r"jobs\.lever\.co/([^/?#]+)", re.IGNORECASE
    ),
    # https://jobs.ashbyhq.com/{slug}[/...]
    "ashby": re.compile(
        r"jobs\.ashbyhq\.com/([^/?#]+)", re.IGNORECASE
    ),
}

# ---------------------------------------------------------------------------
# API URL templates — keyed by provider
# ---------------------------------------------------------------------------

_API_TEMPLATES: dict[str, str] = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
    "lever":      "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby":      "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true",
}


def detect_ats_provider(url: Optional[str]) -> Optional[str]:
    """Return the ATS provider name for a job posting URL, or None if unknown.

    Matching is case-insensitive.  Returns the provider slug string
    (e.g. ``"greenhouse"``, ``"lever"``).

    Args:
        url: The job posting URL to inspect.  May be ``None`` or empty.

    Returns:
        Provider name string, or ``None`` if no pattern matches.

    Examples:
        >>> detect_ats_provider("https://boards.greenhouse.io/airbnb/jobs/123")
        'greenhouse'
        >>> detect_ats_provider("https://example.com/careers")
        None
    """
    if not url:
        return None

    for provider, pattern in _ATS_PATTERNS:
        if pattern.search(url):
            return provider

    return None


def get_company_slug_from_url(url: Optional[str], provider: str) -> Optional[str]:
    """Extract the company slug from a job posting URL for a known provider.

    Only Greenhouse, Lever, and Ashby have predictable slug positions;
    all other providers return ``None``.

    Args:
        url:      The job posting URL.
        provider: ATS provider name (e.g. ``"greenhouse"``).

    Returns:
        Company slug string, or ``None`` if extraction is not possible.

    Examples:
        >>> get_company_slug_from_url("https://boards.greenhouse.io/airbnb/jobs/123", "greenhouse")
        'airbnb'
    """
    if not url:
        return None

    pattern = _SLUG_PATTERNS.get(provider)
    if pattern is None:
        return None

    match = pattern.search(url)
    if match:
        # group(1) is always the slug in our patterns
        slug = match.group(1)
        # Guard against empty strings that could arise from malformed URLs
        return slug if slug else None

    return None


def build_api_url(provider: str, slug: str) -> Optional[str]:
    """Build the canonical API URL for a supported provider + company slug.

    Only Greenhouse, Lever, and Ashby are supported; all others return ``None``.

    Args:
        provider: ATS provider name (e.g. ``"greenhouse"``).
        slug:     Company slug (e.g. ``"airbnb"``).

    Returns:
        Formatted API URL string, or ``None`` for unsupported providers.

    Examples:
        >>> build_api_url("greenhouse", "airbnb")
        'https://boards-api.greenhouse.io/v1/boards/airbnb/jobs?content=true'
        >>> build_api_url("workday", "company")
        None
    """
    template = _API_TEMPLATES.get(provider)
    if template is None:
        return None

    return template.format(slug=slug)
