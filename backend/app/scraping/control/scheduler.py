"""Scoring-based target scheduler for batch selection."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.scraping.control.priority_scorer import compute_priority_score


def _validated_interval_minutes(interval: int | None) -> int:
    """Clamp scheduler intervals to a positive minimum."""
    return max(1, int(interval or 0))


def select_due_targets(
    targets: list,
    batch_size: int = 50,
    now: datetime | None = None,
) -> list:
    """Select targets that are due for scraping, sorted by priority score.

    A target is due if:
    - enabled=True AND quarantined=False
    - next_scheduled_at is None (never scheduled) OR next_scheduled_at <= now
    """
    now = now or datetime.now(UTC)

    due = []
    for t in targets:
        if not t.enabled or t.quarantined:
            continue
        if t.next_scheduled_at is None or t.next_scheduled_at <= now:
            due.append(t)

    # Sort by priority score (highest first)
    due.sort(key=lambda t: compute_priority_score(t), reverse=True)

    return due[:batch_size]


def compute_next_run(target, success: bool) -> datetime:
    """Compute next_scheduled_at based on outcome."""
    now = datetime.now(UTC)
    interval = _validated_interval_minutes(target.schedule_interval_m)

    if success:
        return now + timedelta(minutes=interval)
    else:
        # Exponential backoff on failure, capped at 8x interval
        backoff_multiplier = min(2**target.consecutive_failures, 8)
        return now + timedelta(minutes=interval * backoff_multiplier)
