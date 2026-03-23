"""Standalone script: import H1B sponsor career pages into scrape_targets.

Usage (from D:/jobradar-v2/backend):
    $env:JR_H1B_EXCEL_PATH = "D:/path/to/H1B_Sponsors_Career_Pages.xlsx"
    $env:JR_H1B_USER_EMAIL = "user@example.com"
    python -m scripts.import_h1b_targets
"""

from __future__ import annotations

import asyncio
import os
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

import openpyxl  # type: ignore[import-untyped]
from sqlalchemy import select, text

# Import auth models first so SQLAlchemy registers the `users` table in metadata
# before we try to flush ScrapeTarget rows (which have a FK to users.id).
from app.auth import models as auth_models
from app.database import async_session_factory
from app.scraping.control.classifier import assign_priority, classify_target
from app.scraping.models import ScrapeTarget

_ = auth_models.User

if TYPE_CHECKING:
    from app.profile.models import UserProfile

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_EXCEL_PATH = _BACKEND_ROOT / "data" / "H1B_Sponsors_Career_Pages.xlsx"
_EXCEL_PATH_ENV = "JR_H1B_EXCEL_PATH"
_USER_EMAIL_ENV = "JR_H1B_USER_EMAIL"

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
type ExcelRow = tuple[object, ...]


class ParsedRow(TypedDict):
    url: str
    company_name: str | None
    industry: str | None
    lca_filings: int | None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_excel_path() -> Path:
    configured_path = os.environ.get(_EXCEL_PATH_ENV, "").strip()
    if configured_path:
        return Path(configured_path).expanduser().resolve()
    if _DEFAULT_EXCEL_PATH.exists():
        return _DEFAULT_EXCEL_PATH
    raise RuntimeError(
        f"Set {_EXCEL_PATH_ENV} to the workbook path or place the file at {_DEFAULT_EXCEL_PATH}.",
    )


def _get_user_email() -> str:
    user_email = os.environ.get(_USER_EMAIL_ENV, "").strip()
    if not user_email:
        raise RuntimeError(f"Set {_USER_EMAIL_ENV} to the user email that owns the targets.")
    return user_email


def _load_excel(path: Path) -> list[ExcelRow]:
    """Return all data rows from the Excel file."""
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=DATA_START_ROW, values_only=True))
    wb.close()
    return rows


def _parse_row(row: ExcelRow) -> ParsedRow | None:
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
    lca_filings: int | None = None
    if lca_raw is not None:
        try:
            lca_filings = int(str(lca_raw).strip())
        except ValueError:
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
    excel_path = _get_excel_path()
    user_email = _get_user_email()

    print(f"Loading Excel: {excel_path}")
    rows = _load_excel(excel_path)
    print(f"Found {len(rows)} data rows (from row {DATA_START_ROW})")

    async with async_session_factory() as db:
        # ---- Look up user by email ----
        result = await db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": user_email},
        )
        row = result.first()
        if row is None:
            raise RuntimeError(f"No user found with email {user_email!r}.")
        user_id: uuid.UUID = row[0]
        print(f"Found user id: {user_id}")

        # ---- Load watchlist from user profile (if available) ----
        user_profile_model: type[UserProfile] | None
        try:
            from app.profile.models import UserProfile as UserProfileModel  # noqa: PLC0415
        except ImportError:
            user_profile_model = None
        else:
            user_profile_model = UserProfileModel

        db_watchlist: list[str] = []
        if user_profile_model is not None:
            profile = await db.scalar(
                select(user_profile_model).where(user_profile_model.user_id == user_id)
            )
            if profile and profile.watchlist_companies:
                db_watchlist = profile.watchlist_companies

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
