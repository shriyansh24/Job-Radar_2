from datetime import UTC, datetime
from types import SimpleNamespace

from app.scraping.control.priority_scorer import compute_priority_score


def _target(**kw):
    defaults = dict(
        priority_class="cool",
        consecutive_failures=0,
        last_success_tier=1,
        last_success_at=None,
        next_scheduled_at=None,
        schedule_interval_m=720,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def test_watchlist_highest():
    assert compute_priority_score(_target(priority_class="watchlist")) > compute_priority_score(
        _target(priority_class="hot")
    )


def test_hot_above_warm():
    assert compute_priority_score(_target(priority_class="hot")) > compute_priority_score(
        _target(priority_class="warm")
    )


def test_never_scraped_gets_bonus():
    never = compute_priority_score(_target(last_success_at=None))
    recent = compute_priority_score(_target(last_success_at=datetime.now(UTC)))
    assert never > recent


def test_failures_reduce_score():
    clean = compute_priority_score(_target(consecutive_failures=0))
    failing = compute_priority_score(_target(consecutive_failures=5))
    assert clean > failing


def test_expensive_tier_penalized():
    cheap = compute_priority_score(_target(last_success_tier=0))
    expensive = compute_priority_score(_target(last_success_tier=3))
    assert cheap > expensive


def test_overdue_bonus_requires_both_fields():
    """Overdue bonus only applies when BOTH last_success_at and next_scheduled_at exist."""
    # Has last_success_at but no next_scheduled_at — should NOT crash
    score = compute_priority_score(
        _target(
            last_success_at=datetime.now(UTC),
            next_scheduled_at=None,
        )
    )
    assert isinstance(score, (int, float))
