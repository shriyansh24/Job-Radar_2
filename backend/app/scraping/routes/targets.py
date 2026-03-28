from __future__ import annotations

import uuid

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.scraping.models import ScrapeAttempt, ScraperRun, ScrapeTarget
from app.scraping.schemas import (
    ScrapeAttemptResponse,
    ScrapeTargetImportItem,
    ScrapeTargetImportResponse,
    ScrapeTargetListResponse,
    ScrapeTargetReleaseRequest,
    ScrapeTargetResponse,
    ScrapeTargetUpdate,
    ScrapeTargetWithAttemptsResponse,
    TriggerBatchRequest,
    TriggerBatchResponse,
)
from app.shared.errors import NotFoundError

target_scraper_router = APIRouter()


@target_scraper_router.get("/targets", response_model=ScrapeTargetListResponse)
async def list_targets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    priority_class: str | None = Query(None),
    ats_vendor: str | None = Query(None),
    quarantined: bool | None = Query(None),
    enabled: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> ScrapeTargetListResponse:
    """List all scrape targets for the current user with optional filters."""
    base_query = select(ScrapeTarget).where(ScrapeTarget.user_id == user.id)

    if priority_class is not None:
        base_query = base_query.where(ScrapeTarget.priority_class == priority_class)
    if ats_vendor is not None:
        base_query = base_query.where(ScrapeTarget.ats_vendor == ats_vendor)
    if quarantined is not None:
        base_query = base_query.where(ScrapeTarget.quarantined == quarantined)
    if enabled is not None:
        base_query = base_query.where(ScrapeTarget.enabled == enabled)

    total = await db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    rows_result = await db.scalars(
        base_query.order_by(ScrapeTarget.created_at.desc()).offset(offset).limit(limit)
    )
    items = [ScrapeTargetResponse.model_validate(target) for target in rows_result.all()]

    return ScrapeTargetListResponse(items=items, total=total)


@target_scraper_router.get("/targets/{target_id}", response_model=ScrapeTargetWithAttemptsResponse)
async def get_target(
    target_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScrapeTargetWithAttemptsResponse:
    """Get a single scrape target with its last 5 attempts."""
    result = await db.execute(
        select(ScrapeTarget).where(
            ScrapeTarget.id == target_id,
            ScrapeTarget.user_id == user.id,
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise NotFoundError(f"Target {target_id} not found")

    attempts_result = await db.scalars(
        select(ScrapeAttempt)
        .where(ScrapeAttempt.target_id == target_id)
        .order_by(ScrapeAttempt.created_at.desc())
        .limit(5)
    )
    recent_attempts = [
        ScrapeAttemptResponse.model_validate(attempt)
        for attempt in attempts_result.all()
    ]

    return ScrapeTargetWithAttemptsResponse(
        target=ScrapeTargetResponse.model_validate(target),
        recent_attempts=recent_attempts,
    )


@target_scraper_router.post(
    "/targets/import",
    response_model=ScrapeTargetImportResponse,
    status_code=201,
)
async def import_targets(
    items: list[ScrapeTargetImportItem],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScrapeTargetImportResponse:
    """Bulk import scrape targets from a JSON list with URL-pattern classification."""
    from datetime import UTC, datetime

    from app.scraping.constants import PRIORITY_INTERVALS
    from app.scraping.control.classifier import classify_target

    imported = 0
    skipped = 0
    errors: list[str] = []

    for item in items:
        url = item.url.strip()
        if not url or not url.startswith("http"):
            errors.append(f"Invalid URL: {item.url!r}")
            continue

        existing = await db.scalar(
            select(ScrapeTarget).where(
                ScrapeTarget.url == url,
                ScrapeTarget.user_id == user.id,
            )
        )
        if existing:
            skipped += 1
            continue

        try:
            classification = classify_target(url, item.company_name)
        except Exception as exc:
            errors.append(f"Classification failed for {url!r}: {exc}")
            continue

        priority_class = item.priority_class or "cool"
        schedule_interval_m = PRIORITY_INTERVALS.get(priority_class, PRIORITY_INTERVALS["cool"])
        ats_vendor = item.ats_vendor or classification.get("ats_vendor")

        target = ScrapeTarget(
            user_id=user.id,
            url=url,
            company_name=item.company_name,
            source_kind=classification.get("source_kind", "career_page"),
            ats_vendor=ats_vendor,
            ats_board_token=classification.get("ats_board_token"),
            start_tier=classification.get("start_tier", 1),
            priority_class=priority_class,
            schedule_interval_m=schedule_interval_m,
            next_scheduled_at=datetime.now(UTC),
        )
        db.add(target)
        imported += 1

    await db.commit()
    return ScrapeTargetImportResponse(imported=imported, skipped=skipped, errors=errors)


@target_scraper_router.post("/targets/{target_id}/trigger", response_model=ScrapeAttemptResponse)
async def trigger_target(
    target_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScrapeAttemptResponse:
    """Force-run a single scrape target immediately."""
    from app.config import settings
    from app.scraping.execution.adapter_registry import build_default_registry
    from app.scraping.execution.browser_pool import BrowserPool
    from app.scraping.service import ScrapingService

    result = await db.execute(
        select(ScrapeTarget).where(
            ScrapeTarget.id == target_id,
            ScrapeTarget.user_id == user.id,
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise NotFoundError(f"Target {target_id} not found")

    run = ScraperRun(
        user_id=user.id,
        source="manual_trigger",
        status="running",
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    service = ScrapingService(db, settings)
    adapter_registry = build_default_registry(settings)
    browser_pool = BrowserPool()

    await service.run_target_batch(
        targets=[target],
        run_id=run.id,
        adapter_registry=adapter_registry,
        browser_pool=browser_pool,
    )

    attempt_result = await db.scalar(
        select(ScrapeAttempt)
        .where(
            ScrapeAttempt.target_id == target_id,
            ScrapeAttempt.run_id == run.id,
        )
        .order_by(ScrapeAttempt.created_at.desc())
        .limit(1)
    )
    if attempt_result is None:
        raise NotFoundError(f"No attempt recorded for target {target_id}")

    return ScrapeAttemptResponse.model_validate(attempt_result)


@target_scraper_router.patch("/targets/{target_id}", response_model=ScrapeTargetResponse)
async def update_target(
    target_id: uuid.UUID,
    data: ScrapeTargetUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScrapeTargetResponse:
    """Update a scrape target's priority_class, enabled, start_tier, or max_tier."""
    result = await db.execute(
        select(ScrapeTarget).where(
            ScrapeTarget.id == target_id,
            ScrapeTarget.user_id == user.id,
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise NotFoundError(f"Target {target_id} not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(target, key, value)

    await db.commit()
    await db.refresh(target)
    return ScrapeTargetResponse.model_validate(target)


@target_scraper_router.post("/targets/{target_id}/release", response_model=ScrapeTargetResponse)
async def release_target(
    target_id: uuid.UUID,
    data: ScrapeTargetReleaseRequest = Body(default_factory=ScrapeTargetReleaseRequest),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScrapeTargetResponse:
    """Release a quarantined target, resetting its failure counters."""
    from datetime import UTC, datetime

    result = await db.execute(
        select(ScrapeTarget).where(
            ScrapeTarget.id == target_id,
            ScrapeTarget.user_id == user.id,
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise NotFoundError(f"Target {target_id} not found")

    target.quarantined = False
    target.quarantine_reason = None
    target.consecutive_failures = 0
    target.next_scheduled_at = datetime.now(UTC)

    if data.force_tier is not None:
        target.start_tier = data.force_tier

    await db.commit()
    await db.refresh(target)
    return ScrapeTargetResponse.model_validate(target)


@target_scraper_router.get("/attempts", response_model=list[ScrapeAttemptResponse])
async def list_attempts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    target_id: uuid.UUID | None = Query(None),
    run_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
) -> list[ScrapeAttemptResponse]:
    """List recent scrape attempts, optionally filtered."""
    query = (
        select(ScrapeAttempt)
        .join(ScrapeTarget, ScrapeAttempt.target_id == ScrapeTarget.id)
        .where(ScrapeTarget.user_id == user.id)
    )

    if target_id is not None:
        query = query.where(ScrapeAttempt.target_id == target_id)
    if run_id is not None:
        query = query.where(ScrapeAttempt.run_id == run_id)
    if status is not None:
        query = query.where(ScrapeAttempt.status == status)

    rows = await db.scalars(query.order_by(ScrapeAttempt.created_at.desc()).limit(limit))
    return [ScrapeAttemptResponse.model_validate(attempt) for attempt in rows.all()]


@target_scraper_router.post("/trigger-batch", response_model=TriggerBatchResponse)
async def trigger_batch(
    data: TriggerBatchRequest = Body(default_factory=TriggerBatchRequest),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TriggerBatchResponse:
    """Trigger a batch scrape run for due targets."""
    from app.config import settings
    from app.scraping.control.scheduler import select_due_targets
    from app.scraping.execution.adapter_registry import build_default_registry
    from app.scraping.execution.browser_pool import BrowserPool
    from app.scraping.service import ScrapingService

    targets_query = select(ScrapeTarget).where(
        ScrapeTarget.user_id == user.id,
        ScrapeTarget.enabled == True,  # noqa: E712
        ScrapeTarget.quarantined == False,  # noqa: E712
    )
    if data.priority_class is not None:
        targets_query = targets_query.where(ScrapeTarget.priority_class == data.priority_class)

    all_targets = list((await db.scalars(targets_query)).all())
    due_targets = select_due_targets(all_targets, batch_size=data.batch_size)

    run = ScraperRun(
        user_id=user.id,
        source="batch_trigger",
        status="running",
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    if not due_targets:
        run.status = "completed"
        run.targets_attempted = 0
        await db.commit()
        return TriggerBatchResponse(
            run_id=run.id,
            targets_attempted=0,
            targets_succeeded=0,
            targets_failed=0,
            jobs_found=0,
            errors=[],
        )

    service = ScrapingService(db, settings)
    adapter_registry = build_default_registry(settings)
    browser_pool = BrowserPool()

    batch_result = await service.run_target_batch(
        targets=due_targets,
        run_id=run.id,
        adapter_registry=adapter_registry,
        browser_pool=browser_pool,
    )

    run.status = "completed"
    run.targets_attempted = batch_result.get("targets_attempted", 0)
    run.targets_succeeded = batch_result.get("targets_succeeded", 0)
    run.targets_failed = batch_result.get("targets_failed", 0)
    run.jobs_found = batch_result.get("jobs_found", 0)
    await db.commit()

    return TriggerBatchResponse(
        run_id=run.id,
        targets_attempted=batch_result.get("targets_attempted", 0),
        targets_succeeded=batch_result.get("targets_succeeded", 0),
        targets_failed=batch_result.get("targets_failed", 0),
        jobs_found=batch_result.get("jobs_found", 0),
        errors=batch_result.get("errors", []),
    )
