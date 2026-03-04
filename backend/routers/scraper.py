import asyncio
import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import ScraperRun
from backend.schemas import ScraperRunRequest, ScraperRunResponse, ScraperStatusResponse
from backend.scheduler import run_scraper, run_all_scrapers, sse_clients

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scraper", tags=["scraper"])


@router.post("/run", response_model=list[ScraperRunResponse])
async def trigger_scraper(body: ScraperRunRequest, db: AsyncSession = Depends(get_db)):
    source = body.source

    async def _run():
        if source == "all":
            await run_all_scrapers()
        else:
            await run_scraper(source)

    asyncio.create_task(_run())

    # Return current runs
    result = await db.execute(
        select(ScraperRun).order_by(ScraperRun.started_at.desc()).limit(10)
    )
    runs = result.scalars().all()
    return [ScraperRunResponse.model_validate(r) for r in runs]


@router.get("/status", response_model=ScraperStatusResponse)
async def get_scraper_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ScraperRun).order_by(ScraperRun.started_at.desc()).limit(20)
    )
    runs = result.scalars().all()

    is_running = any(r.status == "running" for r in runs)

    return ScraperStatusResponse(
        runs=[ScraperRunResponse.model_validate(r) for r in runs],
        is_running=is_running,
    )


@router.get("/stream")
async def scraper_stream():
    queue = asyncio.Queue(maxsize=100)
    sse_clients.append(queue)

    async def event_generator():
        try:
            # Send initial keepalive
            yield f"data: {json.dumps({'event': 'connected'})}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event': 'keepalive'})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            sse_clients.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
