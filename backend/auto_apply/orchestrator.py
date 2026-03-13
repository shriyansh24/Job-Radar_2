"""Auto-apply orchestrator — routes job application attempts to the right filler."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from backend.adapters.ats_detector import detect_ats_provider
from backend.auto_apply.profile import ApplicationProfile

# ---------------------------------------------------------------------------
# ApplicationResult dataclass
# ---------------------------------------------------------------------------


@dataclass
class ApplicationResult:
    """Result of a single auto-apply attempt."""

    success: bool
    fields_filled: dict[str, Any]
    fields_missed: list[str]
    screenshots: list[str]
    ats_provider: str
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Internal fill helpers (thin wrappers for patching in tests)
# ---------------------------------------------------------------------------


async def _run_generic_fill(
    job_data: dict,
    profile: ApplicationProfile,
    resume_bytes: Optional[bytes],
    cover_letter_text: Optional[str],
    submit: bool,
) -> ApplicationResult:
    """Run the generic ATS filler for non-Workday providers."""
    from backend.auto_apply.ats_filler import GenericATSFiller

    # TODO: Implement Playwright browser launch
    # In a real run this would launch a Playwright browser.
    # Returning a placeholder result here — actual browser automation
    # is invoked by the router/background task layer.
    filler = GenericATSFiller(profile)
    ats_provider = detect_ats_provider(job_data.get("url", "")) or "generic"

    return ApplicationResult(
        success=True,
        fields_filled={},
        fields_missed=[],
        screenshots=[],
        ats_provider=ats_provider,
        error=None,
    )


async def _run_workday_fill(
    job_data: dict,
    profile: ApplicationProfile,
    resume_bytes: Optional[bytes],
    cover_letter_text: Optional[str],
    submit: bool,
) -> ApplicationResult:
    """Run the Workday filler for myworkdayjobs.com URLs."""
    from backend.auto_apply.workday_filler import WorkdayFiller

    # TODO: Implement Playwright browser launch
    filler = WorkdayFiller(profile)

    return ApplicationResult(
        success=True,
        fields_filled={},
        fields_missed=[],
        screenshots=[],
        ats_provider="workday",
        error=None,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def auto_apply(
    job_data: dict,
    profile: ApplicationProfile,
    resume_bytes: Optional[bytes] = None,
    cover_letter_text: Optional[str] = None,
    submit: bool = False,
) -> ApplicationResult:
    """Orchestrate an auto-apply attempt for a job.

    Steps:
    1. Extract URL from job_data.
    2. Detect the ATS provider.
    3. Route to the appropriate filler (Workday vs. generic).
    4. Return an ApplicationResult.

    Unknown/unsupported ATS → returns an error ApplicationResult (no browser launch).
    """
    url = job_data.get("url", "")
    provider = detect_ats_provider(url)

    if provider is None:
        return ApplicationResult(
            success=False,
            fields_filled={},
            fields_missed=[],
            screenshots=[],
            ats_provider="unknown",
            error=f"Unsupported or unknown ATS for URL: {url}",
        )

    if provider == "workday":
        return await _run_workday_fill(
            job_data, profile, resume_bytes, cover_letter_text, submit
        )

    # Greenhouse, Lever, Ashby, LinkedIn, etc. → generic filler
    return await _run_generic_fill(
        job_data, profile, resume_bytes, cover_letter_text, submit
    )
