# tests/unit/scraping/test_target_registry.py
"""Tests for target_registry import logic."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from app.scraping.control.target_registry import import_from_excel


def _make_mock_workbook(rows: list[tuple]) -> MagicMock:
    """Create a mock openpyxl workbook returning the given rows."""
    mock_wb = MagicMock()
    mock_ws = MagicMock()
    mock_ws.iter_rows.return_value = rows
    mock_wb.active = mock_ws
    return mock_wb


def _make_mock_db(*, duplicates: set[str] | None = None) -> AsyncMock:
    """Create a mock AsyncSession.

    Args:
        duplicates: set of URLs that should be treated as already existing.
    """
    dups = duplicates or set()
    mock_db = AsyncMock()

    async def _scalar_side_effect(stmt):
        # Extract the URL being checked from the where clause.
        # The first positional clause has .right.value for the URL.
        try:
            clauses = stmt.whereclause
            # Walk the binary expression tree to find url value
            if hasattr(clauses, "clauses"):
                for clause in clauses.clauses:
                    if hasattr(clause, "right") and hasattr(clause.right, "value"):
                        if clause.right.value in dups:
                            return MagicMock()  # existing record
        except Exception:
            pass
        return None

    mock_db.scalar = AsyncMock(return_value=None)
    # db.add() is synchronous in SQLAlchemy, so use a regular MagicMock
    mock_db.add = MagicMock()
    return mock_db


@pytest.mark.asyncio
async def test_import_dry_run_does_not_commit():
    """Dry run should not call db.commit() or db.add()."""
    mock_wb = _make_mock_workbook([
        (1, "Google", "Tech", "https://careers.google.com/jobs", 5000),
        (2, "Meta", "Tech", "https://boards.greenhouse.io/meta", 3000),
    ])
    mock_db = _make_mock_db()

    with patch("app.scraping.control.target_registry.openpyxl") as mock_openpyxl:
        mock_openpyxl.load_workbook.return_value = mock_wb
        stats = await import_from_excel(
            mock_db, "fake.xlsx", uuid.uuid4(), [], dry_run=True
        )

    assert stats["total"] == 2
    assert stats["imported"] == 2
    assert stats["skipped_duplicate"] == 0
    assert stats["skipped_no_url"] == 0
    mock_db.commit.assert_not_awaited()
    mock_db.add.assert_not_called()


@pytest.mark.asyncio
async def test_import_commits_on_real_run():
    """Non-dry-run should call db.add() for each valid row and commit once."""
    mock_wb = _make_mock_workbook([
        (1, "Google", "Tech", "https://careers.google.com/jobs", 5000),
        (2, "Meta", "Tech", "https://boards.greenhouse.io/meta", 3000),
    ])
    mock_db = _make_mock_db()

    with patch("app.scraping.control.target_registry.openpyxl") as mock_openpyxl:
        mock_openpyxl.load_workbook.return_value = mock_wb
        stats = await import_from_excel(
            mock_db, "fake.xlsx", uuid.uuid4(), [], dry_run=False
        )

    assert stats["total"] == 2
    assert stats["imported"] == 2
    assert mock_db.add.call_count == 2
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_import_skips_rows_without_url():
    """Rows with missing or non-HTTP URLs are skipped."""
    mock_wb = _make_mock_workbook([
        (1, "Google", "Tech", "https://careers.google.com/jobs", 5000),
        (2, "BadCo", "Tech", None, 100),           # no URL
        (3, "BadCo2", "Tech", "", 100),             # empty URL
        (4, "BadCo3", "Tech", "not-a-url", 100),    # non-HTTP URL
        (5, "Meta", "Tech", "https://meta.com/careers", 3000),
    ])
    mock_db = _make_mock_db()

    with patch("app.scraping.control.target_registry.openpyxl") as mock_openpyxl:
        mock_openpyxl.load_workbook.return_value = mock_wb
        stats = await import_from_excel(
            mock_db, "fake.xlsx", uuid.uuid4(), [], dry_run=True
        )

    assert stats["total"] == 5
    assert stats["imported"] == 2
    assert stats["skipped_no_url"] == 3


@pytest.mark.asyncio
async def test_import_skips_short_rows():
    """Rows with fewer than 4 columns are silently skipped."""
    mock_wb = _make_mock_workbook([
        (1, "Google", "Tech", "https://careers.google.com/jobs", 5000),
        (2, "Short"),         # too short
        (3, "Short", "Tech"), # still too short
        None,                 # None row
    ])
    mock_db = _make_mock_db()

    with patch("app.scraping.control.target_registry.openpyxl") as mock_openpyxl:
        mock_openpyxl.load_workbook.return_value = mock_wb
        stats = await import_from_excel(
            mock_db, "fake.xlsx", uuid.uuid4(), [], dry_run=True
        )

    assert stats["total"] == 1
    assert stats["imported"] == 1


@pytest.mark.asyncio
async def test_import_skips_duplicates():
    """Rows with URLs already in the database are skipped."""
    mock_wb = _make_mock_workbook([
        (1, "Google", "Tech", "https://careers.google.com/jobs", 5000),
        (2, "Meta", "Tech", "https://meta.com/careers", 3000),
    ])
    mock_db = _make_mock_db()
    # First call returns an existing record, second returns None
    mock_db.scalar = AsyncMock(side_effect=[MagicMock(), None])

    with patch("app.scraping.control.target_registry.openpyxl") as mock_openpyxl:
        mock_openpyxl.load_workbook.return_value = mock_wb
        stats = await import_from_excel(
            mock_db, "fake.xlsx", uuid.uuid4(), [], dry_run=True
        )

    assert stats["total"] == 2
    assert stats["imported"] == 1
    assert stats["skipped_duplicate"] == 1


@pytest.mark.asyncio
async def test_import_handles_missing_lca_filings():
    """Rows without LCA filings column should import with lca_filings=None."""
    mock_wb = _make_mock_workbook([
        (1, "Company", "Tech", "https://example.com/careers"),  # no 5th column
    ])
    mock_db = _make_mock_db()

    with patch("app.scraping.control.target_registry.openpyxl") as mock_openpyxl:
        mock_openpyxl.load_workbook.return_value = mock_wb
        stats = await import_from_excel(
            mock_db, "fake.xlsx", uuid.uuid4(), [], dry_run=False
        )

    assert stats["total"] == 1
    assert stats["imported"] == 1
    # Verify the ScrapeTarget was created with None lca_filings
    added_obj = mock_db.add.call_args[0][0]
    assert added_obj.lca_filings is None


@pytest.mark.asyncio
async def test_import_calls_classification():
    """Import should classify each URL and assign priority."""
    mock_wb = _make_mock_workbook([
        (1, "HugFace", "Tech", "https://boards.greenhouse.io/huggingface", 2000),
    ])
    mock_db = _make_mock_db()

    with patch("app.scraping.control.target_registry.openpyxl") as mock_openpyxl:
        mock_openpyxl.load_workbook.return_value = mock_wb
        stats = await import_from_excel(
            mock_db, "fake.xlsx", uuid.uuid4(), [], dry_run=False
        )

    assert stats["imported"] == 1
    added_obj = mock_db.add.call_args[0][0]
    # Greenhouse URL should be classified
    assert added_obj.ats_vendor == "greenhouse"
    assert added_obj.ats_board_token == "huggingface"
    assert added_obj.start_tier == 0
    assert added_obj.source_kind == "ats_board"
    # 2000 LCA filings => hot priority
    assert added_obj.priority_class == "hot"


@pytest.mark.asyncio
async def test_import_watchlist_priority():
    """Companies on the watchlist should get watchlist priority."""
    mock_wb = _make_mock_workbook([
        (1, "Google", "Tech", "https://careers.google.com/jobs", 50),
    ])
    mock_db = _make_mock_db()

    with patch("app.scraping.control.target_registry.openpyxl") as mock_openpyxl:
        mock_openpyxl.load_workbook.return_value = mock_wb
        stats = await import_from_excel(
            mock_db, "fake.xlsx", uuid.uuid4(), ["Google", "Meta"], dry_run=False
        )

    assert stats["imported"] == 1
    added_obj = mock_db.add.call_args[0][0]
    assert added_obj.priority_class == "watchlist"


@pytest.mark.asyncio
async def test_import_strips_whitespace():
    """URL, company_name, and industry should have whitespace stripped."""
    mock_wb = _make_mock_workbook([
        (1, "  Google  ", "  Tech  ", "  https://careers.google.com/jobs  ", 5000),
    ])
    mock_db = _make_mock_db()

    with patch("app.scraping.control.target_registry.openpyxl") as mock_openpyxl:
        mock_openpyxl.load_workbook.return_value = mock_wb
        stats = await import_from_excel(
            mock_db, "fake.xlsx", uuid.uuid4(), [], dry_run=False
        )

    assert stats["imported"] == 1
    added_obj = mock_db.add.call_args[0][0]
    assert added_obj.url == "https://careers.google.com/jobs"
    assert added_obj.company_name == "Google"
    assert added_obj.industry == "Tech"


@pytest.mark.asyncio
async def test_import_empty_workbook():
    """Empty workbook (no data rows) should return all-zero stats."""
    mock_wb = _make_mock_workbook([])
    mock_db = _make_mock_db()

    with patch("app.scraping.control.target_registry.openpyxl") as mock_openpyxl:
        mock_openpyxl.load_workbook.return_value = mock_wb
        stats = await import_from_excel(
            mock_db, "fake.xlsx", uuid.uuid4(), [], dry_run=False
        )

    assert stats["total"] == 0
    assert stats["imported"] == 0
    assert stats["skipped_duplicate"] == 0
    assert stats["skipped_no_url"] == 0
    mock_db.add.assert_not_called()
    # commit is still called even with 0 imports (idempotent)
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_import_workbook_closed_after_reading():
    """The workbook should be closed after reading rows."""
    mock_wb = _make_mock_workbook([
        (1, "Google", "Tech", "https://careers.google.com/jobs", 5000),
    ])
    mock_db = _make_mock_db()

    with patch("app.scraping.control.target_registry.openpyxl") as mock_openpyxl:
        mock_openpyxl.load_workbook.return_value = mock_wb
        await import_from_excel(
            mock_db, "fake.xlsx", uuid.uuid4(), [], dry_run=True
        )

    mock_wb.close.assert_called_once()
