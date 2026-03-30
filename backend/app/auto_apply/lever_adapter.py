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
    """Submit Lever applications through Lever's public posting API."""

    BASE_URL = "https://api.lever.co/v0/postings"

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    @staticmethod
    def parse_lever_url(url: str) -> tuple[str, str] | None:
        match = _LEVER_URL_RE.search(url)
        if match:
            return match.group("company"), match.group("posting")
        return None

    def _build_profile_payload(self, profile: dict[str, Any]) -> dict[str, str]:
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
            data["phone"] = str(profile["phone"])
        if profile.get("current_company") or profile.get("org"):
            data["org"] = str(profile.get("current_company") or profile.get("org"))

        url_keys = {
            "linkedin_url": "LinkedIn",
            "github_url": "GitHub",
            "portfolio_url": "Portfolio",
            "website_url": "Portfolio",
        }
        for profile_key, lever_label in url_keys.items():
            value = profile.get(profile_key)
            if value:
                data[f"urls[{lever_label}]"] = str(value)

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
        url = f"{self.BASE_URL}/{company_slug}/{posting_id}/apply"
        data = self._build_profile_payload(profile)

        if cover_letter:
            data["comments"] = cover_letter
        if custom_questions:
            data.update(custom_questions)

        files: dict[str, tuple[str, bytes, str]] | None = None
        if resume_path:
            resume_file = Path(resume_path)
            if resume_file.exists():
                content_type = "application/pdf"
                if resume_file.suffix.lower() == ".docx":
                    content_type = (
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                files = {"resume": (resume_file.name, resume_file.read_bytes(), content_type)}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, data=data, files=files or {})
        except httpx.TimeoutException:
            logger.error(
                "auto_apply_lever_timeout",
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
                "auto_apply_lever_http_error",
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

        if response.status_code == 200:
            logger.info(
                "auto_apply_lever_success",
                company=company_slug,
                posting_id=posting_id,
            )
            return ApplicationResult(
                success=True,
                ats="lever",
                method="api",
                response_data=response.json() if response.content else None,
                fields_filled=data,
            )

        logger.warning(
            "auto_apply_lever_failed",
            company=company_slug,
            posting_id=posting_id,
            status=response.status_code,
            body=response.text[:500],
        )
        return ApplicationResult(
            success=False,
            ats="lever",
            method="api",
            error=f"HTTP {response.status_code}: {response.text}",
        )

    async def fetch_posting(self, company_slug: str, posting_id: str) -> dict[str, Any] | None:
        url = f"{self.BASE_URL}/{company_slug}/{posting_id}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
        except httpx.HTTPError as exc:
            logger.warning(
                "auto_apply_lever_fetch_failed",
                company=company_slug,
                posting_id=posting_id,
                error=str(exc),
            )
            return None

        if response.status_code == 200:
            return response.json()
        return None
