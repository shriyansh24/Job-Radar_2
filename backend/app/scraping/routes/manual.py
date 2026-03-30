from __future__ import annotations

import json

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.scraping.models import ScraperRun
from app.scraping.schemas import ScraperRunResponse
from app.shared.events import event_bus

manual_scraper_router = APIRouter()
logger = structlog.get_logger()


@manual_scraper_router.post("/run")
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
    queries = profile.search_queries[:3]

    for query_config in queries:
        query = (
            query_config.get("query", query_config)
            if isinstance(query_config, dict)
            else str(query_config)
        )
        location = query_config.get("location") if isinstance(query_config, dict) else None
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
        except Exception as exc:
            logger.error("manual_scrape_failed", query=query, error=str(exc))
            results.append({"query": query, "error": "Scrape run failed"})

    await service.close()
    return {"status": "ok", "results": results}


@manual_scraper_router.get("/stream")
async def scraper_stream(
    user: User = Depends(get_current_user),
) -> EventSourceResponse:
    """SSE endpoint for real-time scraper updates."""

    async def event_generator():
        async for event in event_bus.subscribe(f"scraper:{user.id}"):
            yield {"event": event.get("type", "message"), "data": json.dumps(event)}

    return EventSourceResponse(event_generator())


@manual_scraper_router.get("/runs", response_model=list[ScraperRunResponse])
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
    return [ScraperRunResponse.model_validate(run) for run in result.all()]
