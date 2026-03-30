from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.enrichment.freshness import compute_freshness_score


def test_one_hour_old() -> None:
    assert compute_freshness_score(datetime.now(UTC) - timedelta(hours=1)) == 1.0


def test_twelve_hours_old() -> None:
    assert compute_freshness_score(datetime.now(UTC) - timedelta(hours=12)) == 0.9


def test_two_days_old() -> None:
    assert compute_freshness_score(datetime.now(UTC) - timedelta(days=2)) == 0.7


def test_five_days_old() -> None:
    assert compute_freshness_score(datetime.now(UTC) - timedelta(days=5)) == 0.5


def test_ten_days_old() -> None:
    assert compute_freshness_score(datetime.now(UTC) - timedelta(days=10)) == 0.3


def test_twenty_days_old() -> None:
    assert compute_freshness_score(datetime.now(UTC) - timedelta(days=20)) == 0.1


def test_sixty_days_old() -> None:
    assert compute_freshness_score(datetime.now(UTC) - timedelta(days=60)) == 0.0


def test_none_returns_default() -> None:
    assert compute_freshness_score(None) == 0.5
