from __future__ import annotations

from datetime import datetime, UTC

BASE_PRIORITY = {"watchlist": 100, "hot": 70, "warm": 40, "cool": 10}


def compute_priority_score(target) -> float:
    score = BASE_PRIORITY.get(target.priority_class, 10)

    # Recency bonus
    if target.last_success_at is None:
        score += 20  # never scraped
    elif target.last_success_at and target.next_scheduled_at:
        # Only compute overdue if BOTH values exist (defensive check)
        overdue = (datetime.now(UTC) - target.next_scheduled_at).total_seconds()
        interval_s = target.schedule_interval_m * 60
        if overdue > interval_s * 2:
            score += 10
        elif overdue > interval_s:
            score += 5

    # Failure penalty
    score -= target.consecutive_failures * 15

    # Cost penalty
    tier = target.last_success_tier or 0
    if tier >= 3:
        score -= 10
    elif tier >= 2:
        score -= 5

    return score
