"""Pipeline state machine: valid statuses and transition rules."""

from __future__ import annotations

from app.shared.errors import ValidationError

VALID_STATUSES: list[str] = [
    "saved", "applied", "screening", "interviewing",
    "offer", "rejected", "withdrawn", "accepted",
]

VALID_TRANSITIONS: dict[str, list[str]] = {
    "saved": ["applied", "withdrawn"],
    "applied": ["screening", "interviewing", "rejected", "withdrawn"],
    "screening": ["interviewing", "rejected", "withdrawn"],
    "interviewing": ["offer", "rejected", "withdrawn"],
    "offer": ["accepted", "rejected", "withdrawn"],
    "accepted": [],
    "rejected": ["saved"],
    "withdrawn": ["saved"],
}


def validate_transition(current_status: str, new_status: str) -> None:
    """Validate a status transition, raising ``ValidationError`` on failure.

    Raises:
        ValidationError: If *new_status* is not a recognised status or the
            transition from *current_status* to *new_status* is not allowed.
    """
    if new_status not in VALID_STATUSES:
        raise ValidationError(f"Invalid status: {new_status}")

    allowed = VALID_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise ValidationError(
            f"Cannot transition from '{current_status}' to '{new_status}'. "
            f"Allowed: {allowed}"
        )
