"""Standalone script: import H1B sponsor career pages into scrape_targets.

Usage (from D:/jobradar-v2/backend):
    python -m scripts.import_h1b_targets
    # or
    python scripts/import_h1b_targets.py
"""

# ruff: noqa: E402

from __future__ import annotations

import asyncio
import sys
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Make sure app is importable when run as a plain script (not -m)
# ---------------------------------------------------------------------------
_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import openpyxl
from sqlalchemy import select, text

# Import auth models first so SQLAlchemy registers the `users` table in metadata
# before we try to flush ScrapeTarget rows (which have a FK to users.id).
import app.auth.models  # noqa: F401
from app.database import async_session_factory
from app.scraping.control.classifier import assign_priority, classify_target
from app.scraping.models import ScrapeTarget

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
EXCEL_PATH = Path("C:/Users/shriy/Downloads/H1B_Sponsors_Career_Pages.xlsx")
USER_EMAIL = "shriyansh.singh24@gmail.com"

# Hard-coded watchlist as a baseline; will be merged with DB watchlist at runtime
BASE_WATCHLIST: list[str] = [
    "Hugging Face",
    "Perplexity",
    "OpenAI",
    "Google",
    "Meta",
    "Uber",
    "Snap Inc",
    "Snap",
    "Lyft",
    "Airbnb",
    "Microsoft",
    "BNSF",
    "Amazon",
]

# Excel layout (0-indexed columns after skipping header rows)
# Row 4 is the header: Rank | Company Name | Industry | Career Page URL |
#                       Total LCA Filings | H1B Grader Profile | Filing Entity Names
COL_RANK = 0
COL_COMPANY = 1
COL_INDUSTRY = 2
COL_URL = 3
COL_LCA = 4
DATA_START_ROW = 5  # 1-indexed; rows 1-4 are metadata/header


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_excel(path: Path) -> list[tuple]:
    """Return all data rows from the Excel file."""
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=DATA_START_ROW, values_only=True))
    wb.close()
    return rows


def _parse_row(row: tuple) -> dict | None:
    """Parse a single Excel row; return None if invalid."""
    if not row or len(row) <= COL_URL:
        return None

    url_raw = row[COL_URL]
    url = str(url_raw).strip() if url_raw else ""
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return None

    company_name_raw = row[COL_COMPANY]
    company_name = str(company_name_raw).strip() if company_name_raw else None

    industry_raw = row[COL_INDUSTRY]
    industry = str(industry_raw).strip() if industry_raw else None

    lca_raw = row[COL_LCA] if len(row) > COL_LCA else None
    try:
        lca_filings = int(lca_raw) if lca_raw is not None else None
    except (ValueError, TypeError):
        lca_filings = None

    return {
        "url": url,
        "company_name": company_name,
        "industry": industry,
        "lca_filings": lca_filings,
    }


# ---------------------------------------------------------------------------
# Main import logic
# ---------------------------------------------------------------------------


async def run_import() -> None:
    print(f"Loading Excel: {EXCEL_PATH}")
    rows = _load_excel(EXCEL_PATH)
    print(f"Found {len(rows)} data rows (from row {DATA_START_ROW})")

    async with async_session_factory() as db:
        # ---- Look up user by email ----
        result = await db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": USER_EMAIL},
        )
        row = result.first()
        if row is None:
            print(f"ERROR: No user found with email '{USER_EMAIL}'")
            sys.exit(1)
        user_id: uuid.UUID = row[0]
        print(f"Found user id: {user_id}")

        # ---- Load watchlist from user profile (if available) ----
        try:
            from app.profile.models import UserProfile  # noqa: PLC0415

            profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
            db_watchlist: list[str] = (
                profile.watchlist_companies if profile and profile.watchlist_companies else []
            )
        except Exception:  # profile model may not exist yet
            db_watchlist = []

        # Merge base watchlist + DB watchlist (deduplicated)
        watchlist = list({*BASE_WATCHLIST, *db_watchlist})
        print(f"Watchlist has {len(watchlist)} entries")

        # ---- Fetch existing URLs for this user (for fast dedup) ----
        existing_urls_result = await db.execute(
            select(ScrapeTarget.url).where(ScrapeTarget.user_id == user_id)
        )
        existing_urls: set[str] = {r[0] for r in existing_urls_result.all()}
        print(f"Existing targets in DB for this user: {len(existing_urls)}")

        # ---- Process rows ----
        stats = {
            "total": 0,
            "imported": 0,
            "skipped_no_url": 0,
            "skipped_duplicate": 0,
        }
        ats_breakdown: dict[str, int] = defaultdict(int)
        priority_breakdown: dict[str, int] = defaultdict(int)
        new_targets: list[ScrapeTarget] = []

        for i, row_data in enumerate(rows):
            parsed = _parse_row(row_data)
            if parsed is None:
                stats["skipped_no_url"] += 1
                continue

            stats["total"] += 1
            url = parsed["url"]

            if url in existing_urls:
                stats["skipped_duplicate"] += 1
                continue

            # Classify ATS vendor
            classification = classify_target(url, parsed["company_name"])
            # Assign priority
            priority = assign_priority(parsed["lca_filings"], parsed["company_name"], watchlist)

            target = ScrapeTarget(
                user_id=user_id,
                url=url,
                company_name=parsed["company_name"],
                industry=parsed["industry"],
                lca_filings=parsed["lca_filings"],
                next_scheduled_at=datetime.now(UTC),
                **classification,
                **priority,
            )
            new_targets.append(target)
            existing_urls.add(url)  # prevent in-batch dupes

            ats_breakdown[classification["ats_vendor"] or "unknown"] += 1
            priority_breakdown[priority["priority_class"]] += 1
            stats["imported"] += 1

            if stats["imported"] % 100 == 0:
                print(
                    f"  Progress: {stats['imported']} staged ({i + 1}/{len(rows)} rows scanned)..."
                )

        # ---- Bulk insert ----
        print(f"\nInserting {len(new_targets)} targets into DB...")
        for t in new_targets:
            db.add(t)
        await db.commit()
        print("Commit successful.")

    # ---- Summary ----
    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(f"  Total rows processed : {stats['total'] + stats['skipped_no_url']}")
    print(f"  Valid rows           : {stats['total']}")
    print(f"  Imported             : {stats['imported']}")
    print(f"  Skipped (duplicate)  : {stats['skipped_duplicate']}")
    print(f"  Skipped (no URL)     : {stats['skipped_no_url']}")

    print("\n  ATS Vendor Breakdown:")
    for vendor, count in sorted(ats_breakdown.items(), key=lambda x: -x[1]):
        print(f"    {vendor:<20} {count}")

    print("\n  Priority Breakdown:")
    for cls, count in sorted(priority_breakdown.items(), key=lambda x: -x[1]):
        print(f"    {cls:<20} {count}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_import())
