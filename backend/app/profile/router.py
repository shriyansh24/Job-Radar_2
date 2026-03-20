from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.profile.schemas import ProfileResponse, ProfileUpdate
from app.profile.service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    svc = ProfileService(db)
    profile = await svc.get_profile(user.id)
    return ProfileResponse.model_validate(profile)


@router.post("/generate-answers")
async def generate_answers(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = ProfileService(db)
    return await svc.generate_answers(user.id)


@router.patch("", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    svc = ProfileService(db)
    profile = await svc.update_profile(data, user.id)
    return ProfileResponse.model_validate(profile)
