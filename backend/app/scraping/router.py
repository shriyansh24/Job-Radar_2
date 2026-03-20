from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.scraping.models import ScrapeTarget, ScraperRun
from app.scraping.schemas import (
    CareerPageCreate,
    CareerPageResponse,
    CareerPageUpdate,
    ScraperRunResponse,
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

    profile = await db.scalar(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
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
            results.append({
                "query": query,
                "jobs_found": getattr(result, "jobs_found", 0),
                "jobs_new": getattr(result, "jobs_new", 0),
            })
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
