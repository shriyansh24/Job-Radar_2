from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class WizardStep(str, Enum):
    PERSONAL_INFO = "personal_info"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    VOLUNTARY_DISCLOSURES = "voluntary_disclosures"
    REVIEW = "review"
    UNKNOWN = "unknown"


@dataclass
class StepResult:
    step: WizardStep
    fields_filled: dict[str, str] = field(default_factory=dict)
    fields_missed: list[str] = field(default_factory=list)
    screenshot: bytes | None = None


@dataclass
class ApplicationResult:
    success: bool
    ats: str = "workday"
    method: str = "browser"
    needs_confirmation: bool = True
    page_reached: int = 0
    steps: list[StepResult] = field(default_factory=list)
    screenshots: list[bytes] = field(default_factory=list)
    error: str | None = None
    review_items: list[str] = field(default_factory=list)

    @property
    def fields_filled(self) -> dict[str, str]:
        merged: dict[str, str] = {}
        for s in self.steps:
            merged.update(s.fields_filled)
        return merged

    @property
    def fields_missed(self) -> list[str]:
        missed: list[str] = []
        for s in self.steps:
            missed.extend(s.fields_missed)
        return missed
