"""Tests for the job freshness scoring function."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.enrichment.freshness import compute_freshness_score


class TestComputeFreshnessScore:
    """Verify discrete freshness tiers."""

    def test_one_hour_old(self) -> None:
        ts = datetime.now(UTC) - timedelta(hours=1)
        assert compute_freshness_score(ts) == 1.0

    def test_twelve_hours_old(self) -> None:
        ts = datetime.now(UTC) - timedelta(hours=12)
        assert compute_freshness_score(ts) == 0.9

    def test_two_days_old(self) -> None:
        ts = datetime.now(UTC) - timedelta(days=2)
        assert compute_freshness_score(ts) == 0.7

    def test_five_days_old(self) -> None:
        ts = datetime.now(UTC) - timedelta(days=5)
        assert compute_freshness_score(ts) == 0.5

    def test_ten_days_old(self) -> None:
        ts = datetime.now(UTC) - timedelta(days=10)
        assert compute_freshness_score(ts) == 0.3

    def test_twenty_days_old(self) -> None:
        ts = datetime.now(UTC) - timedelta(days=20)
        assert compute_freshness_score(ts) == 0.1

    def test_sixty_days_old(self) -> None:
        ts = datetime.now(UTC) - timedelta(days=60)
        assert compute_freshness_score(ts) == 0.0

    def test_none_returns_default(self) -> None:
        assert compute_freshness_score(None) == 0.5
