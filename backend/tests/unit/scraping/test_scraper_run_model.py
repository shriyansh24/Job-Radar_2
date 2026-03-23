"""Tests for ScraperRun model tier counter columns."""

from app.scraping.models import ScraperRun


def test_scraper_run_has_tier_counters():
    """ScraperRun model should have tier execution counter columns."""
    columns = {c.name for c in ScraperRun.__table__.columns}
    tier_cols = {
        "targets_attempted",
        "targets_succeeded",
        "targets_failed",
        "tier_0_count",
        "tier_1_count",
        "tier_2_count",
        "tier_3_count",
        "tier_api_count",
    }
    assert tier_cols.issubset(columns), f"Missing tier counter columns: {tier_cols - columns}"


def test_scraper_run_tier_defaults():
    """Check default values for tier counter columns."""
    col = ScraperRun.__table__.columns
    assert col["targets_attempted"].default.arg == 0
    assert col["targets_succeeded"].default.arg == 0
    assert col["targets_failed"].default.arg == 0
    assert col["tier_0_count"].default.arg == 0
    assert col["tier_1_count"].default.arg == 0
    assert col["tier_2_count"].default.arg == 0
    assert col["tier_3_count"].default.arg == 0
    assert col["tier_api_count"].default.arg == 0
