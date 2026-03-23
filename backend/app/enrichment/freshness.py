"""Job freshness scoring based on first-seen age."""

from __future__ import annotations

from datetime import UTC, datetime


def compute_freshness_score(first_seen_at: datetime | None) -> float:
    """Return a 0.0-1.0 freshness score based on how recently a job was first seen.

    The score decays in discrete tiers:
        < 6 h   -> 1.0
        < 24 h  -> 0.9
        < 72 h  -> 0.7
        < 168 h -> 0.5  (1 week)
        < 336 h -> 0.3  (2 weeks)
        < 720 h -> 0.1  (30 days)
        >= 720 h -> 0.0
    """
    if first_seen_at is None:
        return 0.5

    age_hours = (datetime.now(UTC) - first_seen_at).total_seconds() / 3600

    if age_hours < 6:
        return 1.0
    if age_hours < 24:
        return 0.9
    if age_hours < 72:
        return 0.7
    if age_hours < 168:
        return 0.5
    if age_hours < 336:
        return 0.3
    if age_hours < 720:
        return 0.1
    return 0.0
