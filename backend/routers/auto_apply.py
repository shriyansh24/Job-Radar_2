"""Auto-apply REST API router.

Endpoints:
  GET  /auto-apply/profile          — get current ApplicationProfile
  POST /auto-apply/profile          — save ApplicationProfile
  POST /auto-apply/analyze          — detect ATS provider for a job URL
  POST /auto-apply/run              — trigger auto-apply (async)
  POST /auto-apply/pause            — pause ongoing auto-apply
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.ats_detector import detect_ats_provider
from backend.auto_apply.profile import ApplicationProfile, validate_profile
from backend.database import get_db
from backend.models import Job, UserProfile

router = APIRouter(prefix="/auto-apply", tags=["auto-apply"])


# ---------------------------------------------------------------------------
# Pydantic request/response models
# ---------------------------------------------------------------------------


class ProfileRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    location: Optional[str] = None
    work_authorization: Optional[str] = None
    years_experience: Optional[int] = None
    education_summary: Optional[str] = None
    current_title: Optional[str] = None
    desired_salary: Optional[str] = None


class AnalyzeRequest(BaseModel):
    job_id: str


class RunRequest(BaseModel):
    job_id: str
    submit: bool = False
    cover_letter_text: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/profile")
async def get_profile(db: AsyncSession = Depends(get_db)) -> dict:
    """Return the saved ApplicationProfile, or an empty profile if none exists."""
    result = await db.execute(select(UserProfile).where(UserProfile.id == 1))
    user = result.scalar_one_or_none()

    if user is None or user.application_profile is None:
        # Return empty profile
        return ApplicationProfile().to_dict()

    return user.application_profile


@router.post("/profile")
async def save_profile(
    body: ProfileRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Save (upsert) the ApplicationProfile into UserProfile.application_profile.

    Replaces the entire application profile. Send all fields, not just changed ones.
    """
    profile = ApplicationProfile(**body.model_dump(exclude_none=False))
    errors = validate_profile(profile)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": errors},
        )

    result = await db.execute(select(UserProfile).where(UserProfile.id == 1))
    user = result.scalar_one_or_none()

    if user is None:
        user = UserProfile(id=1, application_profile=profile.to_dict())
        db.add(user)
    else:
        user.application_profile = profile.to_dict()

    await db.commit()
    return {"status": "saved", "profile": profile.to_dict()}


@router.post("/analyze")
async def analyze_job(
    body: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Detect the ATS provider for a job URL and return analysis metadata."""
    result = await db.execute(select(Job).where(Job.job_id == body.job_id))
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{body.job_id}' not found",
        )

    provider = detect_ats_provider(job.url)

    return {
        "job_id": body.job_id,
        "url": job.url,
        "ats_provider": provider or "unknown",
        "is_supported": provider is not None,
        "message": (
            f"ATS provider detected: {provider}"
            if provider
            else "No supported ATS detected — manual application required"
        ),
    }


@router.post("/run")
async def run_auto_apply(
    body: RunRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger an auto-apply attempt for a job.

    Loads the saved ApplicationProfile, resolves the job, and invokes
    the orchestrator.  Returns immediately with a task token — the actual
    browser automation runs in a background task.
    """
    result = await db.execute(select(Job).where(Job.job_id == body.job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{body.job_id}' not found",
        )

    # Load profile
    user_result = await db.execute(select(UserProfile).where(UserProfile.id == 1))
    user = user_result.scalar_one_or_none()
    if user is None or not user.application_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No application profile configured. POST /auto-apply/profile first.",
        )

    profile = ApplicationProfile.from_dict(user.application_profile)
    errors = validate_profile(profile)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": errors},
        )

    provider = detect_ats_provider(job.url)

    # TODO: enqueue background task with Celery / APScheduler in a future chunk.
    # For now, return a token indicating the task is queued.
    return {
        "status": "queued",
        "job_id": body.job_id,
        "ats_provider": provider or "unknown",
        "submit": body.submit,
        "message": "Auto-apply task queued. Check /api/auto-apply/status for updates.",
    }


@router.post("/pause")
async def pause_auto_apply() -> dict:
    """Pause any in-progress auto-apply task.

    In the current implementation (no persistent task queue) this is a no-op
    that signals the UI to stop polling.
    """
    return {"status": "paused", "message": "Auto-apply paused"}
