# app/scraping/control/target_registry.py
"""ScrapeTarget CRUD operations and bulk import."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import openpyxl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.scraping.control.classifier import assign_priority, classify_target
from app.scraping.models import ScrapeTarget


async def import_from_excel(
    db: AsyncSession,
    file_path: str | Path,
    user_id: uuid.UUID,
    watchlist: list[str],
    dry_run: bool = False,
) -> dict:
    """Import H1B career page URLs from Excel file.

    The expected Excel format has header rows 1-4 (skipped).
    Data starts at row 5 with columns:
        rank, company_name, industry, url, lca_filings, ...
    """
    wb = openpyxl.load_workbook(file_path, read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=5, values_only=True))  # skip header rows 1-4
    wb.close()

    stats = {"total": 0, "imported": 0, "skipped_duplicate": 0, "skipped_no_url": 0}

    for row in rows:
        if not row or len(row) < 4:
            continue
        stats["total"] += 1

        rank, company_name, industry, url, *rest = row
        url = str(url).strip() if url else ""
        if not url or not url.startswith("http"):
            stats["skipped_no_url"] += 1
            continue
        company_name = str(company_name).strip() if company_name else None
        industry = str(industry).strip() if industry else None
        lca_filings = int(rest[0]) if rest and rest[0] else None

        # Check for duplicate URL
        existing = await db.scalar(
            select(ScrapeTarget).where(
                ScrapeTarget.url == url, ScrapeTarget.user_id == user_id
            )
        )
        if existing:
            stats["skipped_duplicate"] += 1
            continue

        # Classify
        classification = classify_target(url, company_name)
        priority = assign_priority(lca_filings, company_name, watchlist)

        if not dry_run:
            target = ScrapeTarget(
                user_id=user_id,
                url=url,
                company_name=company_name,
                industry=industry,
                lca_filings=lca_filings,
                next_scheduled_at=datetime.now(UTC),
                **classification,
                **priority,
            )
            db.add(target)
        stats["imported"] += 1

    if not dry_run:
        await db.commit()

    return stats


async def list_targets(
    db: AsyncSession,
    user_id: uuid.UUID,
    priority: str | None = None,
    ats: str | None = None,
    quarantined: bool | None = None,
    failing: bool = False,
    limit: int = 50,
) -> list[ScrapeTarget]:
    """List targets with optional filters."""
    query = select(ScrapeTarget).where(ScrapeTarget.user_id == user_id)
    if priority:
        query = query.where(ScrapeTarget.priority_class == priority)
    if ats:
        query = query.where(ScrapeTarget.ats_vendor == ats)
    if quarantined is not None:
        query = query.where(ScrapeTarget.quarantined == quarantined)
    if failing:
        query = query.where(ScrapeTarget.consecutive_failures > 0)
    query = query.order_by(ScrapeTarget.created_at.desc()).limit(limit)
    result = await db.scalars(query)
    return list(result.all())
