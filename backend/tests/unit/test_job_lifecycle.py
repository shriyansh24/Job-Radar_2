"""Tests for Job model lifecycle tracking columns."""
from app.jobs.models import Job


def test_job_has_lifecycle_columns():
    """Job model should have lifecycle tracking columns."""
    columns = {c.name for c in Job.__table__.columns}
    lifecycle_cols = {
        "first_seen_at",
        "last_seen_at",
        "disappeared_at",
        "content_hash",
        "previous_hash",
        "seen_count",
        "source_target_id",
    }
    assert lifecycle_cols.issubset(columns), (
        f"Missing lifecycle columns: {lifecycle_cols - columns}"
    )


def test_job_lifecycle_defaults():
    """Check default values for lifecycle columns."""
    col = Job.__table__.columns
    assert col["seen_count"].default.arg == 1
