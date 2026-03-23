"""Application validation module.

Validates a filled application form before submission, checking for common
issues: missing required fields, placeholder text, short essays, company mismatches.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger()

_PLACEHOLDER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\[.*?\]"),
    re.compile(r"<.*?>"),
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bFIXME\b", re.IGNORECASE),
    re.compile(r"\bPLACEHOLDER\b", re.IGNORECASE),
    re.compile(r"\bINSERT\s+(HERE|NAME|COMPANY)\b", re.IGNORECASE),
    re.compile(r"\bYOUR\s+(NAME|EMAIL|COMPANY|TITLE)\b", re.IGNORECASE),
    re.compile(r"\bN/A\b", re.IGNORECASE),
    re.compile(r"\.\.\.\s*$"),
]

_REQUIRED_FIELDS: frozenset[str] = frozenset({"full_name", "email", "phone", "resume_upload"})

_ESSAY_KEY_PATTERNS = re.compile(
    r"(essay|cover_letter|why_|motivation|describe|experience|summary|about)",
    re.IGNORECASE,
)
_MIN_ESSAY_CHARS = 50


class IssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ValidationIssue:
    field: str
    message: str
    severity: IssueSeverity = IssueSeverity.ERROR


@dataclass
class ValidationResult:
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    flag_for_review: bool = False

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.WARNING]

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "flag_for_review": self.flag_for_review,
            "errors": [{"field": i.field, "message": i.message} for i in self.errors],
            "warnings": [{"field": i.field, "message": i.message} for i in self.warnings],
        }


class ApplicationValidator:
    """Validates a filled application form dict before submission."""

    def __init__(self, min_essay_chars: int = _MIN_ESSAY_CHARS) -> None:
        self.min_essay_chars = min_essay_chars

    async def validate(self, filled_form: dict, job: dict) -> ValidationResult:
        issues: list[ValidationIssue] = []

        self._check_required_fields(filled_form, issues)
        self._check_resume_attached(filled_form, issues)
        self._check_essay_length(filled_form, issues)
        self._check_placeholder_text(filled_form, issues)
        self._check_company_name(filled_form, job, issues)

        has_errors = any(i.severity == IssueSeverity.ERROR for i in issues)

        result = ValidationResult(
            valid=not has_errors,
            issues=issues,
            flag_for_review=len(issues) > 0,
        )

        if issues:
            logger.info(
                "validator.issues_found",
                total=len(issues),
                errors=len(result.errors),
                warnings=len(result.warnings),
            )

        return result

    def _check_required_fields(self, filled_form: dict, issues: list[ValidationIssue]) -> None:
        for req_field in sorted(_REQUIRED_FIELDS):
            if not filled_form.get(req_field):
                issues.append(
                    ValidationIssue(
                        field=req_field,
                        message=f"Required field '{req_field}' is missing or empty.",
                    )
                )

    def _check_resume_attached(self, filled_form: dict, issues: list[ValidationIssue]) -> None:
        if not filled_form.get("resume_upload"):
            if not any(i.field == "resume_upload" for i in issues):
                issues.append(
                    ValidationIssue(
                        field="resume_upload",
                        message="Resume has not been attached to the application.",
                    )
                )

    def _check_essay_length(self, filled_form: dict, issues: list[ValidationIssue]) -> None:
        for key, value in filled_form.items():
            if not isinstance(value, str):
                continue
            if _ESSAY_KEY_PATTERNS.search(key) or key.startswith("question:"):
                stripped = value.strip()
                if 0 < len(stripped) < self.min_essay_chars:
                    issues.append(
                        ValidationIssue(
                            field=key,
                            message=(
                                f"Essay answer for '{key}' is too short "
                                f"({len(stripped)} chars; minimum {self.min_essay_chars})."
                            ),
                            severity=IssueSeverity.WARNING,
                        )
                    )

    def _check_placeholder_text(self, filled_form: dict, issues: list[ValidationIssue]) -> None:
        for key, value in filled_form.items():
            if not isinstance(value, str):
                continue
            for pattern in _PLACEHOLDER_PATTERNS:
                if pattern.search(value):
                    issues.append(
                        ValidationIssue(
                            field=key,
                            message=f"Field '{key}' contains placeholder text.",
                        )
                    )
                    break

    def _check_company_name(
        self, filled_form: dict, job: dict, issues: list[ValidationIssue]
    ) -> None:
        expected = (job.get("company") or job.get("company_name") or "").strip().lower()
        if not expected:
            return

        for key, value in filled_form.items():
            if not isinstance(value, str):
                continue
            if re.search(r"\bcompany\b", key, re.IGNORECASE):
                filled = value.strip().lower()
                if filled and filled != expected:
                    issues.append(
                        ValidationIssue(
                            field=key,
                            message=(
                                "Company name mismatch: form has "
                                f"'{value}' but job company is "
                                f"'{job.get('company') or job.get('company_name')}'."
                            ),
                            severity=IssueSeverity.WARNING,
                        )
                    )
