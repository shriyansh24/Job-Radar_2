"""Declarative job filter DSL.

A ``JobFilter`` is a plain dataclass that encodes a set of inclusion /
exclusion rules for job objects.  It exposes:

- ``evaluate(job)``      — returns ``(passes: bool, reasons: list[str])``
- ``filter_jobs(jobs)``  — returns the subset of jobs that pass all rules
- ``from_dict(d)``       — constructor from a plain dict (e.g. from JSON)

Design goals
------------
* Pure Python — no database, no async, no I/O.
* Operates on any object with the expected attributes; no ORM dependency.
* Every rejection produces a machine-readable reason string so callers
  can surface filter diagnostics in the UI.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

# ---------------------------------------------------------------------------
# Reason constants (machine-readable reason tags)
# ---------------------------------------------------------------------------

_MISSING_KEYWORD       = "missing_keyword"
_EXCLUDED_KEYWORD      = "excluded_keyword"
_NO_MATCHING_ANY       = "no_matching_keyword_any"
_SALARY_TOO_LOW        = "salary_below_min"
_SALARY_TOO_HIGH       = "salary_above_max"
_NO_SALARY_DATA        = "no_salary_data"
_LOCATION_MISMATCH     = "location_mismatch"
_REMOTE_MISMATCH       = "remote_type_mismatch"
_EMPLOYMENT_MISMATCH   = "employment_type_mismatch"
_SENIORITY_MISMATCH    = "seniority_mismatch"
_TECH_ALL_MISSING      = "tech_stack_missing_required"
_TECH_ANY_MISSING      = "tech_stack_no_match_any"
_COMPANY_EXCLUDED      = "company_excluded"
_POSTED_TOO_OLD        = "posted_too_old"
_SCORE_TOO_LOW         = "match_score_below_min"


def _lower_list(items: list[str]) -> list[str]:
    """Return a copy of a string list with all items lower-cased."""
    return [i.lower() for i in items]


def _text_contains(text: str, term: str) -> bool:
    """Return True if ``term`` appears as a whole word in ``text``."""
    # Use word boundaries to avoid "go" matching inside "golang" etc.
    return bool(re.search(r"\b" + re.escape(term) + r"\b", text, re.IGNORECASE))


def _job_searchable_text(job: Any) -> str:
    """Assemble the full searchable text corpus for a job object."""
    parts: list[str] = []
    for attr in ("title", "title_normalized", "description_plain"):
        val = getattr(job, attr, None)
        if val:
            parts.append(str(val))
    return " ".join(parts)


# ---------------------------------------------------------------------------
# JobFilter
# ---------------------------------------------------------------------------

@dataclass
class JobFilter:
    """Declarative filter for job objects.

    All criteria are combined with AND semantics (every criterion that is
    non-empty must pass).  Within a single list criterion the semantics are:

    * ``keywords_include``     — ALL terms must appear (AND)
    * ``keywords_exclude``     — ANY matching term causes rejection (OR)
    * ``keywords_include_any`` — AT LEAST ONE term must appear (OR)
    * ``tech_stack_all``       — ALL techs must be present (AND)
    * ``tech_stack_any``       — AT LEAST ONE tech must be present (OR)
    * ``locations_include``    — job location must match at least one (OR)
    * ``remote_types``         — job remote_type must be one of these
    * ``employment_types``     — job employment_type must be one of these
    * ``seniority_levels``     — job seniority_level must be one of these
    * ``companies_exclude``    — any matching company causes rejection
    """

    # Keyword filters (operate on title + description text)
    keywords_include:     list[str] = field(default_factory=list)
    keywords_exclude:     list[str] = field(default_factory=list)
    keywords_include_any: list[str] = field(default_factory=list)

    # Salary
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    # If True, jobs with no salary data pass the salary check.
    # If False, they fail when salary_min or salary_max is set.
    require_salary_data: bool = False

    # Location (partial, case-insensitive)
    locations_include: list[str] = field(default_factory=list)

    # Enum-value lists (values compared case-insensitively)
    remote_types:      list[str] = field(default_factory=list)
    employment_types:  list[str] = field(default_factory=list)
    seniority_levels:  list[str] = field(default_factory=list)

    # Tech stack filters (operate on job.tech_stack list)
    tech_stack_all: list[str] = field(default_factory=list)
    tech_stack_any: list[str] = field(default_factory=list)

    # Company exclusions (partial, case-insensitive)
    companies_exclude: list[str] = field(default_factory=list)

    # Recency
    posted_within_days: Optional[int] = None

    # Match score (0–100)
    min_match_score: Optional[float] = None

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------

    def evaluate(self, job: Any) -> tuple[bool, list[str]]:
        """Evaluate a single job against all filter criteria.

        Args:
            job: Any object with the expected attributes.  Missing attributes
                 are treated as ``None`` / empty.

        Returns:
            ``(passes, reasons)`` where ``passes`` is ``True`` if the job
            satisfies every active criterion, and ``reasons`` is a list of
            machine-readable rejection reason strings (empty when passing).
        """
        reasons: list[str] = []

        self._check_keywords_include(job, reasons)
        self._check_keywords_exclude(job, reasons)
        self._check_keywords_include_any(job, reasons)
        self._check_salary(job, reasons)
        self._check_locations(job, reasons)
        self._check_remote_types(job, reasons)
        self._check_employment_types(job, reasons)
        self._check_seniority_levels(job, reasons)
        self._check_tech_stack_all(job, reasons)
        self._check_tech_stack_any(job, reasons)
        self._check_companies_exclude(job, reasons)
        self._check_posted_within(job, reasons)
        self._check_match_score(job, reasons)

        return (len(reasons) == 0, reasons)

    def filter_jobs(self, jobs: Iterable[Any]) -> list[Any]:
        """Return the subset of *jobs* that pass all filter criteria.

        Args:
            jobs: Any iterable of job objects.

        Returns:
            A new list containing only the passing jobs, in original order.
        """
        return [job for job in jobs if self.evaluate(job)[0]]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobFilter":
        """Construct a ``JobFilter`` from a plain dictionary.

        Unknown keys are silently ignored so callers can pass raw request
        bodies without pre-filtering.

        Args:
            data: Dict with keys matching ``JobFilter`` field names.

        Returns:
            A new ``JobFilter`` instance.
        """
        kwargs: dict[str, Any] = {}
        for fld in cls.__dataclass_fields__:  # type: ignore[attr-defined]
            if fld in data:
                kwargs[fld] = data[fld]
        return cls(**kwargs)

    # --------------------------------------------------------------------------
    # Private check helpers
    # --------------------------------------------------------------------------

    def _check_keywords_include(self, job: Any, reasons: list[str]) -> None:
        if not self.keywords_include:
            return
        text = _job_searchable_text(job)
        for term in self.keywords_include:
            if not _text_contains(text, term):
                reasons.append(f"{_MISSING_KEYWORD}:{term}")

    def _check_keywords_exclude(self, job: Any, reasons: list[str]) -> None:
        if not self.keywords_exclude:
            return
        text = _job_searchable_text(job)
        for term in self.keywords_exclude:
            if _text_contains(text, term):
                reasons.append(f"{_EXCLUDED_KEYWORD}:{term}")

    def _check_keywords_include_any(self, job: Any, reasons: list[str]) -> None:
        if not self.keywords_include_any:
            return
        text = _job_searchable_text(job)
        for term in self.keywords_include_any:
            if _text_contains(text, term):
                return  # at least one matched
        reasons.append(f"{_NO_MATCHING_ANY}:{','.join(self.keywords_include_any)}")

    def _check_salary(self, job: Any, reasons: list[str]) -> None:
        has_min = self.salary_min is not None
        has_max = self.salary_max is not None
        if not has_min and not has_max:
            return

        job_min: Optional[float] = getattr(job, "salary_min", None)
        job_max: Optional[float] = getattr(job, "salary_max", None)

        # No salary data on the job
        if job_min is None and job_max is None:
            if self.require_salary_data:
                reasons.append(_NO_SALARY_DATA)
            # else: no salary data → pass silently (permissive default)
            return

        # Use the best available salary value for comparison.
        # salary_max is preferred because it represents the ceiling offer;
        # fall back to salary_min when salary_max is absent.
        best: float = job_max if job_max is not None else job_min  # type: ignore[assignment]

        if has_min and best < self.salary_min:  # type: ignore[operator]
            reasons.append(f"{_SALARY_TOO_LOW}:{best}")

        if has_max and best > self.salary_max:  # type: ignore[operator]
            reasons.append(f"{_SALARY_TOO_HIGH}:{best}")

    def _check_locations(self, job: Any, reasons: list[str]) -> None:
        if not self.locations_include:
            return

        # Try location_normalized first, then location
        loc_value: str = (
            getattr(job, "location_normalized", None)
            or getattr(job, "location", None)
            or ""
        )
        loc_lower = loc_value.lower()

        for loc_term in self.locations_include:
            if loc_term.lower() in loc_lower:
                return  # at least one matched

        reasons.append(f"{_LOCATION_MISMATCH}:{loc_value!r}")

    def _check_remote_types(self, job: Any, reasons: list[str]) -> None:
        if not self.remote_types:
            return
        job_remote: Optional[str] = getattr(job, "remote_type", None)
        if job_remote is None:
            return
        if job_remote.lower() not in _lower_list(self.remote_types):
            reasons.append(f"{_REMOTE_MISMATCH}:{job_remote}")

    def _check_employment_types(self, job: Any, reasons: list[str]) -> None:
        if not self.employment_types:
            return
        job_emp: Optional[str] = getattr(job, "employment_type", None)
        if job_emp is None:
            return
        if job_emp.lower() not in _lower_list(self.employment_types):
            reasons.append(f"{_EMPLOYMENT_MISMATCH}:{job_emp}")

    def _check_seniority_levels(self, job: Any, reasons: list[str]) -> None:
        if not self.seniority_levels:
            return
        job_sen: Optional[str] = getattr(job, "seniority_level", None)
        if job_sen is None:
            return
        if job_sen.lower() not in _lower_list(self.seniority_levels):
            reasons.append(f"{_SENIORITY_MISMATCH}:{job_sen}")

    def _check_tech_stack_all(self, job: Any, reasons: list[str]) -> None:
        if not self.tech_stack_all:
            return
        job_stack: list[str] = getattr(job, "tech_stack", None) or []
        job_stack_lower = _lower_list(job_stack)
        missing = [t for t in self.tech_stack_all if t.lower() not in job_stack_lower]
        if missing:
            reasons.append(f"{_TECH_ALL_MISSING}:{','.join(missing)}")

    def _check_tech_stack_any(self, job: Any, reasons: list[str]) -> None:
        if not self.tech_stack_any:
            return
        job_stack: list[str] = getattr(job, "tech_stack", None) or []
        job_stack_lower = _lower_list(job_stack)
        for tech in self.tech_stack_any:
            if tech.lower() in job_stack_lower:
                return
        reasons.append(f"{_TECH_ANY_MISSING}:{','.join(self.tech_stack_any)}")

    def _check_companies_exclude(self, job: Any, reasons: list[str]) -> None:
        if not self.companies_exclude:
            return
        company: str = (
            getattr(job, "company_normalized", None)
            or getattr(job, "company", None)
            or ""
        )
        company_lower = company.lower()
        for exc in self.companies_exclude:
            if exc.lower() in company_lower:
                reasons.append(f"{_COMPANY_EXCLUDED}:{company!r}")
                return

    def _check_posted_within(self, job: Any, reasons: list[str]) -> None:
        if self.posted_within_days is None:
            return
        posted_at: Optional[datetime] = getattr(job, "posted_at", None)
        if posted_at is None:
            return  # no date → pass (permissive)
        now = datetime.now(timezone.utc)
        # Make posted_at timezone-aware if naive
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        age_days = (now - posted_at).days
        if age_days > self.posted_within_days:
            reasons.append(f"{_POSTED_TOO_OLD}:{age_days}d")

    def _check_match_score(self, job: Any, reasons: list[str]) -> None:
        if self.min_match_score is None:
            return
        score: Optional[float] = getattr(job, "match_score", None)
        if score is None:
            return  # no score → pass (permissive)
        if score < self.min_match_score:
            reasons.append(f"{_SCORE_TOO_LOW}:{score}")
