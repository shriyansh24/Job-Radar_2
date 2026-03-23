"""Company / Title / Location normalization utilities (Feature A2).

Each normalizer is a lightweight, stateless class that reduces noisy scraped
strings to canonical forms suitable for deduplication and grouping.
"""

from __future__ import annotations

import re
import unicodedata

# ---------------------------------------------------------------------------
# Company normalization
# ---------------------------------------------------------------------------

COMPANY_SUFFIXES: set[str] = {
    "inc",
    "corp",
    "corporation",
    "llc",
    "ltd",
    "limited",
    "gmbh",
    "ag",
    "sa",
    "plc",
    "co",
    "com",
    "company",
    "group",
    "holdings",
    "technologies",
    "tech",
    "labs",
    "software",
    "systems",
    "solutions",
    "services",
}

# Well-known aliases that fuzzy matching alone would miss.
_COMPANY_ALIASES: dict[str, str] = {
    "alphabet": "google",
    "meta platforms": "meta",
    "microsoft corporation": "microsoft",
    "amazon.com": "amazon",
    "ibm corporation": "ibm",
}

# ---------------------------------------------------------------------------
# Title normalization
# ---------------------------------------------------------------------------

TITLE_ABBREVIATIONS: dict[str, str] = {
    "sr": "senior",
    "sr.": "senior",
    "jr": "junior",
    "jr.": "junior",
    "ml": "machine learning",
    "eng": "engineer",
    "eng.": "engineer",
    "engr": "engineer",
    "mgr": "manager",
    "dir": "director",
    "vp": "vice president",
    "svp": "senior vice president",
    "evp": "executive vice president",
    "swe": "software engineer",
    "sde": "software development engineer",
    "pm": "product manager",
    "tpm": "technical program manager",
    "ds": "data scientist",
    "de": "data engineer",
    "qa": "quality assurance",
    "ui": "user interface",
    "ux": "user experience",
    "fe": "frontend",
    "be": "backend",
    "fs": "fullstack",
    "devops": "development operations",
    "ops": "operations",
    "admin": "administrator",
    "assoc": "associate",
    "asst": "assistant",
    "dept": "department",
    "exec": "executive",
    "hr": "human resources",
    "it": "information technology",
}

# Regex that matches level indicators (roman numerals i-v, digits 1-5,
# and common level words) when they appear as whole words.
LEVEL_PATTERNS: re.Pattern[str] = re.compile(
    r"\b(?:i{1,3}|iv|v|[1-5]"
    r"|staff|principal|lead|senior|junior|entry[- ]?level|intern|mid[- ]?level"
    r")\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Location normalization
# ---------------------------------------------------------------------------

LOCATION_ALIASES: dict[str, str] = {
    "sf": "san francisco",
    "nyc": "new york city",
    "ny": "new york",
    "la": "los angeles",
    "dc": "washington dc",
    "philly": "philadelphia",
    "chi": "chicago",
    "atl": "atlanta",
    "det": "detroit",
    "bos": "boston",
    "den": "denver",
    "sea": "seattle",
    "pdx": "portland",
    "slc": "salt lake city",
    "rdu": "raleigh-durham",
    "dfw": "dallas-fort worth",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nfkd(text: str) -> str:
    """Unicode NFKD normalize and strip diacritics."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


_PUNCT_RE = re.compile(r"[.,;!?\"'`\[\]{}()|/\\]")
_MULTI_SPACE = re.compile(r"\s+")


def _clean(text: str) -> str:
    """Lowercase, strip accents, remove common punctuation, collapse whitespace."""
    text = _nfkd(text).lower()
    text = _PUNCT_RE.sub(" ", text)
    return _MULTI_SPACE.sub(" ", text).strip()


# ---------------------------------------------------------------------------
# Normalizer classes
# ---------------------------------------------------------------------------

class CompanyNormalizer:
    """Reduce company names to a canonical lowercase form."""

    def normalize(self, name: str | None) -> str:
        if not name:
            return ""
        cleaned = _clean(name)
        # Strip trailing suffixes (may appear with or without leading comma)
        tokens = cleaned.split()
        while tokens and tokens[-1] in COMPANY_SUFFIXES:
            tokens.pop()
        result = " ".join(tokens)
        # Apply hard-coded alias overrides
        return _COMPANY_ALIASES.get(result, result)


class TitleNormalizer:
    """Expand abbreviations in job titles."""

    def normalize(self, title: str | None) -> str:
        if not title:
            return ""
        cleaned = _clean(title)
        tokens = cleaned.split()
        expanded = [TITLE_ABBREVIATIONS.get(tok, tok) for tok in tokens]
        return " ".join(expanded)


class TitleNormalizerStripped(TitleNormalizer):
    """Like TitleNormalizer but also strips level indicators."""

    def normalize(self, title: str | None) -> str:
        base = super().normalize(title)
        stripped = LEVEL_PATTERNS.sub("", base)
        return _MULTI_SPACE.sub(" ", stripped).strip()


class LocationNormalizer:
    """Standardize location strings."""

    def normalize(self, location: str | None) -> str:
        if not location:
            return ""
        cleaned = _clean(location)
        # Try whole-string alias first, then token-level
        if cleaned in LOCATION_ALIASES:
            return LOCATION_ALIASES[cleaned]
        tokens = cleaned.split()
        expanded = [LOCATION_ALIASES.get(tok, tok) for tok in tokens]
        return " ".join(expanded)
