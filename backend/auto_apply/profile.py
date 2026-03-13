"""Application profile for auto-apply form filling."""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict, fields as dataclass_fields


@dataclass
class ApplicationProfile:
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    location: str | None = None
    work_authorization: str | None = None
    years_experience: int | None = None
    education_summary: str | None = None
    current_title: str | None = None
    desired_salary: str | None = None

    def to_dict(self) -> dict:
        """Return a dict of non-None fields."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, d: dict) -> "ApplicationProfile":
        """Create an ApplicationProfile from a dict, ignoring unknown keys."""
        valid_fields = {f.name for f in dataclass_fields(cls)}
        filtered = {k: v for k, v in d.items() if k in valid_fields}
        return cls(**filtered)


# ---------------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------------

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_profile(profile: ApplicationProfile) -> list[str]:
    """Validate an ApplicationProfile and return a list of error messages.

    Returns an empty list if the profile is valid.
    """
    errors: list[str] = []

    if not profile.name:
        errors.append("Name is required")

    if not profile.email:
        errors.append("Email is required")
    elif not EMAIL_REGEX.match(profile.email):
        errors.append("Email format is invalid")

    return errors
