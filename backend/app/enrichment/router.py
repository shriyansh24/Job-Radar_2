from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


@router.post("/enrich/{job_id}")
async def enrich_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger enrichment for a single job. Implementation in Phase 3B."""
    return {
        "status": "pending",
        "job_id": job_id,
        "message": "Enrichment service pending Phase 3B",
    }


@router.post("/batch")
async def batch_enrich(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger batch enrichment. Implementation in Phase 3B."""
    return {"status": "pending", "message": "Batch enrichment pending Phase 3B"}


@router.get("/system/gpu-status")
async def gpu_status(
    user: User = Depends(get_current_user),
) -> dict:
    """Return Intel GPU availability and device information."""
    from app.enrichment.gpu_accelerator import gpu_accelerator

    info = gpu_accelerator.get_device_info()
    return {
        "gpu_available": gpu_accelerator.is_available(),
        "device_info": asdict(info),
    }
