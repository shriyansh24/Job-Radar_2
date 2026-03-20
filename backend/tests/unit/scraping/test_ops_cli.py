# tests/unit/scraping/test_ops_cli.py
"""Unit tests for CLI ops commands (quarantine, health, test-fetch).

These tests exercise the test-fetch dry-run path which is pure logic
(no DB required). DB-dependent commands (quarantine list/review/release,
health) are tested via integration tests.
"""
from __future__ import annotations

from typer.testing import CliRunner

from app.scraping.ops import app

runner = CliRunner()


def test_test_fetch_dry_run_greenhouse():
    """Greenhouse URL should be classified as ATS with tier 0."""
    result = runner.invoke(
        app, ["test-fetch", "https://boards.greenhouse.io/example", "--dry-run"]
    )
    assert result.exit_code == 0
    assert "greenhouse" in result.output.lower()
    assert "Dry run" in result.output


def test_test_fetch_dry_run_unknown():
    """Unknown career page should be classified with unknown ATS."""
    result = runner.invoke(
        app, ["test-fetch", "https://careers.example.com", "--dry-run"]
    )
    assert result.exit_code == 0
    assert "unknown" in result.output.lower()


def test_test_fetch_dry_run_with_tier():
    """Forced tier should appear in output."""
    result = runner.invoke(
        app,
        ["test-fetch", "https://example.com", "--tier", "2", "--dry-run"],
    )
    assert result.exit_code == 0
    # The forced tier should show up in the plan
    assert "2" in result.output


def test_test_fetch_dry_run_lever():
    """Lever URL should be classified as ATS with tier 0."""
    result = runner.invoke(
        app, ["test-fetch", "https://jobs.lever.co/company", "--dry-run"]
    )
    assert result.exit_code == 0
    assert "lever" in result.output.lower()
    assert "Dry run" in result.output


def test_test_fetch_dry_run_shows_scraper_name():
    """Dry run output should include the primary scraper name."""
    result = runner.invoke(
        app, ["test-fetch", "https://boards.greenhouse.io/test", "--dry-run"]
    )
    assert result.exit_code == 0
    # Greenhouse uses the "greenhouse" scraper
    assert "greenhouse" in result.output.lower()


def test_test_fetch_dry_run_career_page_shows_fallback():
    """Career page dry run should show fallback chain."""
    result = runner.invoke(
        app, ["test-fetch", "https://careers.example.com/jobs", "--dry-run"]
    )
    assert result.exit_code == 0
    # Career pages get a fallback chain
    assert "allback" in result.output  # "Fallback" with capital F


def test_health_command_exists():
    """Health command should be registered on the app."""
    result = runner.invoke(app, ["health", "--help"])
    assert result.exit_code == 0
    assert "success" in result.output.lower() or "health" in result.output.lower()


def test_quarantine_list_help():
    """Quarantine list command should show help."""
    result = runner.invoke(app, ["quarantine", "list", "--help"])
    assert result.exit_code == 0
    assert "quarantined" in result.output.lower()


def test_quarantine_review_help():
    """Quarantine review command should show help."""
    result = runner.invoke(app, ["quarantine", "review", "--help"])
    assert result.exit_code == 0


def test_quarantine_release_help():
    """Quarantine release command should show help."""
    result = runner.invoke(app, ["quarantine", "release", "--help"])
    assert result.exit_code == 0
