from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.scraping.models import ScrapeAttempt, ScraperRun, ScrapeTarget
from app.scraping.schemas import (
    CareerPageCreate,
    CareerPageResponse,
    CareerPageUpdate,
    ScrapeAttemptResponse,
    ScraperRunResponse,
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
from app.shared.events import event_bus

router = APIRouter(prefix="/scraper", tags=["scraper"])


@router.post("/run")
async def trigger_scrape(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manually trigger a scrape run using profile search queries."""
    from app.config import settings
    from app.profile.models import UserProfile
    from app.scraping.service import ScrapingService

    profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    if not profile or not profile.search_queries:
        return {"status": "error", "message": "No search queries configured in your profile"}

    service = ScrapingService(db, settings)
    results = []
    queries = profile.search_queries[:3]  # Limit to first 3 to avoid long waits

    for q in queries:
        query = q.get("query", q) if isinstance(q, dict) else str(q)
        location = q.get("location") if isinstance(q, dict) else None
        if not query:
            continue
        try:
            result = await service.run_scrape(
                query=query,
                location=location,
                user_id=user.id,
            )
            results.append(
                {
                    "query": query,
                    "jobs_found": getattr(result, "jobs_found", 0),
                    "jobs_new": getattr(result, "jobs_new", 0),
                }
            )
        except Exception as e:
            results.append({"query": query, "error": str(e)})

    await service.close()
    return {"status": "ok", "results": results}


@router.get("/stream")
async def scraper_stream(
    user: User = Depends(get_current_user),
) -> EventSourceResponse:
    """SSE endpoint for real-time scraper updates."""

    async def event_generator():
        async for event in event_bus.subscribe(f"scraper:{user.id}"):
            yield {"event": event.get("type", "message"), "data": json.dumps(event)}

    return EventSourceResponse(event_generator())


@router.get("/runs", response_model=list[ScraperRunResponse])
async def list_runs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
) -> list[ScraperRunResponse]:
    result = await db.scalars(
        select(ScraperRun)
        .where(ScraperRun.user_id == user.id)
        .order_by(ScraperRun.started_at.desc())
        .limit(limit)
    )
    return [ScraperRunResponse.model_validate(r) for r in result.all()]


@router.get("/career-pages", response_model=list[CareerPageResponse])
async def list_career_pages(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CareerPageResponse]:
    result = await db.scalars(
        select(ScrapeTarget)
        .where(
            ScrapeTarget.user_id == user.id,
            ScrapeTarget.source_kind == "career_page",
        )
        .order_by(ScrapeTarget.created_at.desc())
    )
    return [CareerPageResponse.model_validate(cp) for cp in result.all()]


@router.post("/career-pages", response_model=CareerPageResponse, status_code=201)
async def create_career_page(
    data: CareerPageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CareerPageResponse:
    target = ScrapeTarget(
        user_id=user.id,
        url=data.url,
        company_name=data.company_name,
        source_kind="career_page",
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return CareerPageResponse.model_validate(target)


@router.patch("/career-pages/{page_id}", response_model=CareerPageResponse)
async def update_career_page(
    page_id: uuid.UUID,
    data: CareerPageUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CareerPageResponse:
    result = await db.execute(
        select(ScrapeTarget).where(
            ScrapeTarget.id == page_id,
            ScrapeTarget.user_id == user.id,
            ScrapeTarget.source_kind == "career_page",
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise NotFoundError(f"Career page {page_id} not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(target, key, value)
    await db.commit()
    await db.refresh(target)
    return CareerPageResponse.model_validate(target)


@router.delete("/career-pages/{page_id}", status_code=204, response_model=None)
async def delete_career_page(
    page_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(ScrapeTarget).where(
            ScrapeTarget.id == page_id,
            ScrapeTarget.user_id == user.id,
            ScrapeTarget.source_kind == "career_page",
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise NotFoundError(f"Career page {page_id} not found")
    await db.delete(target)
    await db.commit()


# ---------------------------------------------------------------------------
# ScrapeTarget endpoints
# ---------------------------------------------------------------------------


@router.get("/targets", response_model=ScrapeTargetListResponse)
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

    # Count total matching rows
    count_result = await db.scalar(select(func.count()).select_from(base_query.subquery()))
    total = count_result or 0

    # Fetch page
    rows_result = await db.scalars(
        base_query.order_by(ScrapeTarget.created_at.desc()).offset(offset).limit(limit)
    )
    items = [ScrapeTargetResponse.model_validate(t) for t in rows_result.all()]

    return ScrapeTargetListResponse(items=items, total=total)


@router.get("/targets/{target_id}", response_model=ScrapeTargetWithAttemptsResponse)
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
    recent_attempts = [ScrapeAttemptResponse.model_validate(a) for a in attempts_result.all()]

    return ScrapeTargetWithAttemptsResponse(
        target=ScrapeTargetResponse.model_validate(target),
        recent_attempts=recent_attempts,
    )


@router.post("/targets/import", response_model=ScrapeTargetImportResponse, status_code=201)
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

        # Check for duplicate URL belonging to this user
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

        # Allow caller to override priority_class and ats_vendor
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


@router.post("/targets/{target_id}/trigger", response_model=ScrapeAttemptResponse)
async def trigger_target(
    target_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScrapeAttemptResponse:
    """Force-run a single scrape target immediately."""
    from app.config import settings
    from app.scraping.execution.adapter_registry import build_default_registry
    from app.scraping.execution.browser_pool import BrowserPool
    from app.scraping.models import ScraperRun
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

    # Create a one-off run record
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

    # Return the most recent attempt for this target under this run
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


@router.patch("/targets/{target_id}", response_model=ScrapeTargetResponse)
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


@router.post("/targets/{target_id}/release", response_model=ScrapeTargetResponse)
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


# ---------------------------------------------------------------------------
# ScrapeAttempt endpoints
# ---------------------------------------------------------------------------


@router.get("/attempts", response_model=list[ScrapeAttemptResponse])
async def list_attempts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    target_id: uuid.UUID | None = Query(None),
    run_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
) -> list[ScrapeAttemptResponse]:
    """List recent scrape attempts, optionally filtered."""
    # Build a sub-select joining through ScrapeTarget to enforce user ownership
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

    query = query.order_by(ScrapeAttempt.created_at.desc()).limit(limit)

    rows = await db.scalars(query)
    return [ScrapeAttemptResponse.model_validate(a) for a in rows.all()]


# ---------------------------------------------------------------------------
# Batch trigger endpoint
# ---------------------------------------------------------------------------


@router.post("/trigger-batch", response_model=TriggerBatchResponse)
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
    from app.scraping.models import ScraperRun
    from app.scraping.service import ScrapingService

    # Fetch eligible targets for this user
    targets_query = select(ScrapeTarget).where(
        ScrapeTarget.user_id == user.id,
        ScrapeTarget.enabled == True,  # noqa: E712
        ScrapeTarget.quarantined == False,  # noqa: E712
    )
    if data.priority_class is not None:
        targets_query = targets_query.where(ScrapeTarget.priority_class == data.priority_class)

    all_targets_result = await db.scalars(targets_query)
    all_targets = list(all_targets_result.all())

    due_targets = select_due_targets(all_targets, batch_size=data.batch_size)

    # Create a run record
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

    # Update the run record with summary counters
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
