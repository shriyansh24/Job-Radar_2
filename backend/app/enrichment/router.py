from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.config import settings
from app.dependencies import get_current_user, get_db
from app.enrichment.llm_client import LLMClient
from app.enrichment.service import EnrichmentService
from app.jobs.models import Job
from app.runtime.queue import enqueue_registered_job
from app.shared.errors import NotFoundError

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


@router.post("/enrich/{job_id}")
async def enrich_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run enrichment for a single owned job."""
    job = await db.scalar(select(Job).where(Job.id == job_id, Job.user_id == user.id))
    if job is None:
        raise NotFoundError(detail=f"Job {job_id} not found")

    llm_client = LLMClient(settings.openrouter_api_key, settings.default_llm_model)
    try:
        service = EnrichmentService(db, llm_client, settings)
        await service.enrich_job(job)
        await db.commit()
        await db.refresh(job)
    finally:
        await llm_client.close()

    return {
        "status": "completed",
        "job_id": job.id,
        "is_enriched": bool(job.is_enriched),
        "enriched_at": job.enriched_at.isoformat() if job.enriched_at is not None else None,
    }


@router.post("/batch")
async def batch_enrich(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Queue a background enrichment batch for the current workspace."""
    request_id = getattr(request.state, "request_id", None)
    dispatch = await enqueue_registered_job(
        "enrichment_batch",
        correlation_id=request_id,
    )
    return {
        "status": "queued",
        "job_name": dispatch.job_name,
        "queue_name": dispatch.queue_name,
        "enqueued_job_id": dispatch.enqueued_job_id,
        "request_id": request_id,
        "queue_depth_after": dispatch.queue_depth_after,
        "queue_pressure_after": dispatch.queue_pressure_after,
        "queue_alert_after": dispatch.queue_alert_after,
    }


@router.get("/system/gpu-status")
async def gpu_status(
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    """Return Intel GPU availability and device information."""
    from app.enrichment.gpu_accelerator import gpu_accelerator

    info = gpu_accelerator.get_device_info()
    return {
        "gpu_available": gpu_accelerator.is_available(),
        "device_info": asdict(info),
    }
