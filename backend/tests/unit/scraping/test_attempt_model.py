"""Unit tests for ScrapeAttempt model structure (no DB required)."""
from __future__ import annotations

import uuid

from app.scraping.models import ScrapeAttempt


def test_scrape_attempt_column_defaults():
    """Check default values are set via mapped_column(default=...) for SQL INSERT."""
    col = ScrapeAttempt.__table__.columns
    assert col["status"].default.arg == "pending"
    assert col["retries"].default.arg == 0
    assert col["escalations"].default.arg == 0
    assert col["jobs_extracted"].default.arg == 0
    assert col["browser_used"].default.arg is False


def test_scrape_attempt_instantiation():
    """ScrapeAttempt can be instantiated with required fields."""
    attempt = ScrapeAttempt(
        target_id=uuid.uuid4(),
        selected_tier=1,
        actual_tier_used=2,
        scraper_name="nodriver",
    )
    assert attempt.scraper_name == "nodriver"
    assert attempt.selected_tier == 1
    assert attempt.actual_tier_used == 2


def test_scrape_attempt_status_values():
    """Valid status values per spec."""
    valid = {"pending", "success", "partial", "failed", "skipped", "escalated", "not_modified"}
    attempt = ScrapeAttempt(
        target_id=uuid.uuid4(), selected_tier=1, actual_tier_used=1, scraper_name="test"
    )
    for status in valid:
        attempt.status = status  # should not raise


def test_scrape_attempt_tablename():
    """Table name must be 'scrape_attempts'."""
    assert ScrapeAttempt.__tablename__ == "scrape_attempts"


def test_scrape_attempt_has_required_columns():
    """ScrapeAttempt should have all columns defined in spec."""
    columns = {c.name for c in ScrapeAttempt.__table__.columns}
    required = {
        "id", "run_id", "target_id", "selected_tier", "actual_tier_used",
        "scraper_name", "parser_name", "status", "http_status",
        "duration_ms", "retries", "escalations", "jobs_extracted",
        "content_hash_before", "content_hash_after", "content_changed",
        "pages_crawled", "pagination_stopped_reason",
        "error_class", "error_message", "browser_used", "created_at",
    }
    assert required.issubset(columns), f"Missing columns: {required - columns}"


def test_scrape_attempt_foreign_keys():
    """ScrapeAttempt should have foreign keys to scraper_runs and scrape_targets."""
    col = ScrapeAttempt.__table__.columns
    run_fks = [fk.target_fullname for fk in col["run_id"].foreign_keys]
    target_fks = [fk.target_fullname for fk in col["target_id"].foreign_keys]
    assert "scraper_runs.id" in run_fks
    assert "scrape_targets.id" in target_fks


def test_scrape_attempt_datetime_timezone():
    """All DateTime columns must use timezone=True."""
    from sqlalchemy import DateTime
    col = ScrapeAttempt.__table__.columns
    assert isinstance(col["created_at"].type, DateTime)
    assert col["created_at"].type.timezone is True
