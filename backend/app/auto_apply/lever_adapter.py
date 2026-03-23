"""Lever API adapter for zero-browser job applications.

Lever's public posting API accepts multipart form POST requests,
making it the fastest and most reliable ATS adapter (~1s per application).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()

_LEVER_URL_RE = re.compile(
    r"(?:https?://)?jobs\.lever\.co/(?P<company>[^/]+)/(?P<posting>[0-9a-f-]+)",
    re.IGNORECASE,
)


@dataclass
class ApplicationResult:
    """Result of an adapter application attempt."""

    success: bool
    ats: str
    method: str
    error: str | None = None
    response_data: dict[str, Any] | None = None
    screenshot: bytes | None = None
    screenshots: list[bytes] | None = None
    needs_confirmation: bool = False
    fields_filled: dict[str, str] = field(default_factory=dict)
    fields_missed: list[str] = field(default_factory=list)
    blocked_by: list[str] | None = None


class LeverAPIAdapter:
    """Submit applications via Lever's public posting API. No browser needed."""

    BASE_URL = "https://api.lever.co/v0/postings"

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    @staticmethod
    def parse_lever_url(url: str) -> tuple[str, str] | None:
        """Extract (company_slug, posting_id) from a Lever URL.

        Returns None if the URL is not a recognized Lever posting URL.
        """
        m = _LEVER_URL_RE.search(url)
        if m:
            return m.group("company"), m.group("posting")
        return None

    def _build_profile_payload(self, profile: dict[str, Any]) -> dict[str, str]:
        """Build the multipart form data dict from a profile."""
        first_name = profile.get("first_name", "")
        last_name = profile.get("last_name", "")
        full_name = profile.get("full_name", "")
        if not full_name and (first_name or last_name):
            full_name = f"{first_name} {last_name}".strip()

        data: dict[str, str] = {
            "name": full_name,
            "email": profile.get("email", ""),
        }
        if profile.get("phone"):
            data["phone"] = profile["phone"]
        if profile.get("current_company") or profile.get("org"):
            data["org"] = profile.get("current_company") or profile.get("org", "")

        # URLs dict — Lever expects urls[LinkedIn], urls[GitHub], etc.
        url_keys = {
            "linkedin_url": "LinkedIn",
            "github_url": "GitHub",
            "portfolio_url": "Portfolio",
            "website_url": "Portfolio",
        }
        for profile_key, lever_label in url_keys.items():
            val = profile.get(profile_key)
            if val:
                data[f"urls[{lever_label}]"] = val

        return data

    async def apply(
        self,
        company_slug: str,
        posting_id: str,
        profile: dict[str, Any],
        resume_path: str | None = None,
        cover_letter: str | None = None,
        custom_questions: dict[str, str] | None = None,
    ) -> ApplicationResult:
        """Submit an application to a Lever posting via API.

        Args:
            company_slug: Lever company slug (from URL).
            posting_id: Lever posting UUID (from URL).
            profile: Applicant profile dict with name, email, phone, etc.
            resume_path: Local filesystem path to the resume file.
            cover_letter: Optional cover letter text.
            custom_questions: Optional dict of custom question answers.

        Returns:
            ApplicationResult with success/failure details.
        """
        url = f"{self.BASE_URL}/{company_slug}/{posting_id}/apply"
        data = self._build_profile_payload(profile)

        if cover_letter:
            data["comments"] = cover_letter

        if custom_questions:
            for key, value in custom_questions.items():
                data[key] = value

        files: dict[str, tuple[str, bytes, str]] | None = None
        if resume_path:
            resume_file = Path(resume_path)
            if resume_file.exists():
                content_type = "application/pdf"
                if resume_file.suffix.lower() == ".docx":
                    content_type = (
                        "application/vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document"
                    )
                files = {"resume": (resume_file.name, resume_file.read_bytes(), content_type)}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, data=data, files=files or {})

            if resp.status_code == 200:
                logger.info(
                    "lever.apply.success",
                    company=company_slug,
                    posting_id=posting_id,
                )
                return ApplicationResult(
                    success=True,
                    ats="lever",
                    method="api",
                    response_data=resp.json() if resp.content else None,
                    fields_filled=data,
                )
            else:
                error_msg = f"HTTP {resp.status_code}: {resp.text}"
                logger.warning(
                    "lever.apply.failed",
                    company=company_slug,
                    posting_id=posting_id,
                    status=resp.status_code,
                    body=resp.text[:500],
                )
                return ApplicationResult(
                    success=False,
                    ats="lever",
                    method="api",
                    error=error_msg,
                )

        except httpx.TimeoutException:
            logger.error(
                "lever.apply.timeout",
                company=company_slug,
                posting_id=posting_id,
            )
            return ApplicationResult(
                success=False,
                ats="lever",
                method="api",
                error="Request timed out",
            )
        except httpx.HTTPError as exc:
            logger.error(
                "lever.apply.http_error",
                company=company_slug,
                posting_id=posting_id,
                error=str(exc),
            )
            return ApplicationResult(
                success=False,
                ats="lever",
                method="api",
                error=f"HTTP error: {exc}",
            )

    async def fetch_posting(
        self, company_slug: str, posting_id: str
    ) -> dict[str, Any] | None:
        """Fetch posting details from Lever's public API.

        Returns the posting JSON or None if not found.
        """
        url = f"{self.BASE_URL}/{company_slug}/{posting_id}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
        except httpx.HTTPError:
            pass
        return None
