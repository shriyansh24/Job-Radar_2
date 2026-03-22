import pytest
from datetime import datetime, timedelta, UTC
from types import SimpleNamespace
from app.scraping.control.scheduler import select_due_targets, compute_next_run


def _target(**kw):
    defaults = dict(
        id="t1",
        priority_class="cool",
        schedule_interval_m=720,
        next_scheduled_at=datetime.now(UTC) - timedelta(hours=1),
        enabled=True,
        quarantined=False,
        consecutive_failures=0,
        last_success_at=None,
        last_success_tier=1,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def test_selects_overdue_targets():
    """Targets past their next_scheduled_at should be selected."""
    overdue = _target(next_scheduled_at=datetime.now(UTC) - timedelta(hours=2))
    future = _target(id="t2", next_scheduled_at=datetime.now(UTC) + timedelta(hours=2))
    selected = select_due_targets([overdue, future])
    assert len(selected) == 1
    assert selected[0].id == "t1"


def test_never_scheduled_always_due():
    """Targets with next_scheduled_at=None are always due."""
    never = _target(next_scheduled_at=None)
    selected = select_due_targets([never])
    assert len(selected) == 1


def test_disabled_excluded():
    """Disabled targets should not be selected."""
    disabled = _target(enabled=False)
    selected = select_due_targets([disabled])
    assert len(selected) == 0


def test_quarantined_excluded():
    """Quarantined targets should not be selected."""
    quarantined = _target(quarantined=True)
    selected = select_due_targets([quarantined])
    assert len(selected) == 0


def test_sorted_by_priority_score():
    """Results should be sorted by priority score (highest first)."""
    watchlist = _target(id="w", priority_class="watchlist")
    cool = _target(id="c", priority_class="cool")
    selected = select_due_targets([cool, watchlist])
    assert selected[0].id == "w"


def test_batch_limit():
    """Should respect batch_size limit."""
    targets = [_target(id=f"t{i}") for i in range(20)]
    selected = select_due_targets(targets, batch_size=5)
    assert len(selected) == 5


def test_compute_next_run_success():
    """After success, next run = now + schedule_interval_m."""
    target = _target(schedule_interval_m=120)
    next_at = compute_next_run(target, success=True)
    expected_min = datetime.now(UTC) + timedelta(minutes=119)
    expected_max = datetime.now(UTC) + timedelta(minutes=121)
    assert expected_min <= next_at <= expected_max


def test_compute_next_run_failure_backoff():
    """After failure, next run uses exponential backoff."""
    target = _target(schedule_interval_m=120, consecutive_failures=3)
    next_at = compute_next_run(target, success=False)
    # Backoff: interval * min(2^failures, 8) = 120 * min(8, 8) = 960 minutes
    expected_min = datetime.now(UTC) + timedelta(minutes=900)
    assert next_at > expected_min


def test_compute_next_run_clamps_invalid_intervals():
    """Zero or negative intervals should fall back to a 1-minute minimum."""
    zero_target = _target(schedule_interval_m=0)
    negative_target = _target(schedule_interval_m=-15)

    zero_next = compute_next_run(zero_target, success=True)
    negative_next = compute_next_run(negative_target, success=False)

    zero_min = datetime.now(UTC) + timedelta(seconds=30)
    negative_min = datetime.now(UTC) + timedelta(seconds=30)

    assert zero_next >= zero_min
    assert negative_next >= negative_min
