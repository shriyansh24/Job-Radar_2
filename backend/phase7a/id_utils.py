"""Shared ID generation and normalization utilities for Phase 7A.

All deterministic IDs use SHA256(key)[:64] to produce a 64-char hex string.
Normalization helpers ensure consistent inputs to hash functions.
"""

import hashlib
import re
import uuid
from urllib.parse import urlparse


# --- Normalization helpers ---

# Seniority prefixes stripped during title normalization
_SENIORITY_PREFIXES = [
    "principal", "staff", "senior", "sr.", "sr", "lead",
    "junior", "jr.", "jr", "associate", "intern",
]

# Company name suffixes stripped during normalization
_COMPANY_SUFFIXES = re.compile(
    r",?\s*\b(inc\.?|incorporated|llc|ltd\.?|limited|corp\.?|corporation"
    r"|co\.?|company|group|holdings|plc|gmbh|ag|sa|sas|bv|nv)\s*$",
    re.IGNORECASE,
)


def normalize_domain(domain: str) -> str:
    """Normalize a domain for consistent company ID generation.

    Strips protocol, www prefix, trailing slashes, and lowercases.

    Examples:
        "https://www.Stripe.COM/jobs" -> "stripe.com"
        "WWW.stripe.com" -> "stripe.com"
        "stripe.com" -> "stripe.com"
    """
    d = domain.strip().lower()
    if "://" in d:
        d = urlparse(d).hostname or d
    d = d.removeprefix("www.")
    d = d.rstrip("/")
    return d


def normalize_company_name(name: str) -> str:
    """Normalize a company name for consistent matching.

    Lowercases, strips legal suffixes (Inc, LLC, Corp, etc.), and trims whitespace.

    Examples:
        "Stripe, Inc." -> "stripe"
        "Acme Corporation" -> "acme"
        "OpenAI" -> "openai"
    """
    n = name.strip().lower()
    n = _COMPANY_SUFFIXES.sub("", n).strip()
    n = re.sub(r"\s+", " ", n)
    return n


def normalize_title(title: str) -> str:
    """Normalize a job title for canonical ID generation.

    Lowercases, strips seniority prefixes, collapses whitespace.

    Examples:
        "Senior Machine Learning Engineer" -> "machine learning engineer"
        "Sr. ML Engineer" -> "ml engineer"
        "Staff Backend Developer" -> "backend developer"
    """
    t = title.strip().lower()
    t = re.sub(r"\s+", " ", t)
    for prefix in _SENIORITY_PREFIXES:
        pattern = re.compile(r"^" + re.escape(prefix) + r"\.?\s+", re.IGNORECASE)
        t = pattern.sub("", t)
    return t.strip()


def normalize_location(location: str) -> str:
    """Normalize a location string for canonical ID generation.

    Extracts the city portion or returns "remote" for remote positions.

    Examples:
        "San Francisco, CA, US" -> "san francisco"
        "Remote" -> "remote"
        "New York, NY" -> "new york"
        "London, United Kingdom" -> "london"
        "" -> ""
    """
    loc = location.strip().lower()
    if not loc:
        return ""
    if "remote" in loc:
        return "remote"
    city = loc.split(",")[0].strip()
    return city


# --- ID generation functions ---

def _sha256_id(key: str) -> str:
    """Compute SHA256 hash and return first 64 hex characters."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:64]


def compute_company_id(domain_or_name: str) -> str:
    """Generate a deterministic company ID from domain or name.

    Uses domain if it looks like one (contains a dot), otherwise uses name.
    Input is normalized before hashing.

    Returns:
        64-char hex string.
    """
    value = domain_or_name.strip()
    if "." in value and " " not in value:
        normalized = normalize_domain(value)
    else:
        normalized = normalize_company_name(value)
    return _sha256_id(normalized)


def compute_source_id(source_type: str, url: str) -> str:
    """Generate a deterministic source ID from type and URL.

    Returns:
        64-char hex string.
    """
    key = f"{source_type.strip().lower()}:{url.strip()}"
    return _sha256_id(key)


def compute_raw_job_id(source: str, source_job_id: str) -> str:
    """Generate a deterministic raw job source ID.

    Returns:
        64-char hex string.
    """
    key = f"{source.strip().lower()}:{source_job_id.strip()}"
    return _sha256_id(key)


def compute_canonical_job_id(company_id: str, title: str, location: str) -> str:
    """Generate a deterministic canonical job ID.

    Normalizes title and location before hashing for stable identity
    across sources with slightly different formatting.

    Returns:
        64-char hex string.
    """
    normalized_title = normalize_title(title)
    normalized_location = normalize_location(location)
    key = f"{company_id}:{normalized_title}:{normalized_location}"
    return _sha256_id(key)


def compute_template_id(intent: str) -> str:
    """Generate a deterministic query template ID from user intent.

    Returns:
        64-char hex string.
    """
    normalized = intent.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    return _sha256_id(normalized)


def generate_application_id() -> str:
    """Generate a unique application ID using UUID4.

    Applications are user-initiated, not deterministic, so UUID is appropriate.

    Returns:
        32-char hex string (UUID4 without dashes).
    """
    return uuid.uuid4().hex
