"""Unit tests for ScrapeTarget model structure (no DB required)."""

from __future__ import annotations

from app.scraping.models import ScrapeTarget


def test_scrape_target_has_required_columns():
    """ScrapeTarget should have all columns defined in spec."""
    columns = {c.name for c in ScrapeTarget.__table__.columns}
    required = {
        "id",
        "user_id",
        "url",
        "company_name",
        "ats_vendor",
        "ats_board_token",
        "start_tier",
        "max_tier",
        "priority_class",
        "schedule_interval_m",
        "enabled",
        "quarantined",
        "content_hash",
        "consecutive_failures",
        "next_scheduled_at",
        "lca_filings",
    }
    assert required.issubset(columns), f"Missing columns: {required - columns}"


def test_scrape_target_column_defaults():
    """Check default values are set via mapped_column(default=...)."""
    col = ScrapeTarget.__table__.columns
    assert col["start_tier"].default.arg == 1
    assert col["max_tier"].default.arg == 3
    assert col["priority_class"].default.arg == "cool"
    assert col["schedule_interval_m"].default.arg == 720
    assert col["enabled"].default.arg is True
    assert col["quarantined"].default.arg is False


def test_scrape_target_with_ats():
    """ScrapeTarget can be instantiated with ATS-specific fields."""
    target = ScrapeTarget(
        url="https://boards.greenhouse.io/huggingface",
        company_name="Hugging Face",
        ats_vendor="greenhouse",
        ats_board_token="huggingface",
        start_tier=0,
        priority_class="watchlist",
        schedule_interval_m=120,
    )
    assert target.ats_vendor == "greenhouse"
    assert target.ats_board_token == "huggingface"
    assert target.start_tier == 0


def test_scrape_target_tablename():
    """Table name must be 'scrape_targets'."""
    assert ScrapeTarget.__tablename__ == "scrape_targets"


def test_scrape_target_has_additional_columns():
    """ScrapeTarget should have all additional columns from spec."""
    columns = {c.name for c in ScrapeTarget.__table__.columns}
    additional = {
        "company_domain",
        "source_kind",
        "quarantine_reason",
        "last_success_at",
        "last_failure_at",
        "last_success_tier",
        "last_http_status",
        "etag",
        "last_modified",
        "failure_count",
        "industry",
        "created_at",
        "updated_at",
    }
    assert additional.issubset(columns), f"Missing columns: {additional - columns}"


def test_scrape_target_datetime_timezone():
    """All DateTime columns must use timezone=True."""
    from sqlalchemy import DateTime

    col = ScrapeTarget.__table__.columns
    datetime_cols = [
        "last_success_at",
        "last_failure_at",
        "next_scheduled_at",
        "created_at",
        "updated_at",
    ]
    for name in datetime_cols:
        assert isinstance(col[name].type, DateTime), f"{name} should be DateTime"
        assert col[name].type.timezone is True, f"{name} must have timezone=True"


def test_scrape_target_indexes():
    """ScrapeTarget should have the required indexes."""
    index_names = {idx.name for idx in ScrapeTarget.__table__.indexes}
    assert "idx_targets_schedule" in index_names
    assert "idx_targets_ats" in index_names
    assert "idx_targets_active" in index_names
