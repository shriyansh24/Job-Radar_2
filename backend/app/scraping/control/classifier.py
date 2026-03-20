"""Target classification: ATS type + priority assignment."""
from __future__ import annotations

from difflib import SequenceMatcher

from app.scraping.constants import PRIORITY_INTERVALS
from app.scraping.control.ats_registry import classify_url


def classify_target(url: str, company_name: str | None = None) -> dict:
    """Classify a target URL into ATS type and source kind."""
    ats = classify_url(url)
    return {
        "ats_vendor": ats.vendor,
        "ats_board_token": ats.board_token,
        "start_tier": ats.start_tier,
        "source_kind": "ats_board" if ats.vendor is not None else "career_page",
    }


def assign_priority(
    lca_filings: int | None,
    company_name: str | None,
    watchlist: list[str],
) -> dict:
    """Assign priority class and schedule interval."""
    filings = lca_filings or 0

    # Watchlist override: fuzzy match against dream companies
    if company_name and watchlist:
        for w in watchlist:
            if _fuzzy_match(company_name, w):
                return {
                    "priority_class": "watchlist",
                    "schedule_interval_m": PRIORITY_INTERVALS["watchlist"],
                }

    if filings >= 1000:
        cls = "hot"
    elif filings >= 100:
        cls = "warm"
    else:
        cls = "cool"

    return {
        "priority_class": cls,
        "schedule_interval_m": PRIORITY_INTERVALS[cls],
    }


def _fuzzy_match(a: str, b: str, threshold: float = 0.8) -> bool:
    """Case-insensitive fuzzy match."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold
