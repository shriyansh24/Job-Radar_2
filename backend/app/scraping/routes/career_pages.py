from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.scraping.models import ScrapeTarget
from app.scraping.schemas import CareerPageCreate, CareerPageResponse, CareerPageUpdate
from app.shared.errors import NotFoundError

career_pages_router = APIRouter()


@career_pages_router.get("/career-pages", response_model=list[CareerPageResponse])
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
    return [CareerPageResponse.model_validate(page) for page in result.all()]


@career_pages_router.post("/career-pages", response_model=CareerPageResponse, status_code=201)
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


@career_pages_router.patch("/career-pages/{page_id}", response_model=CareerPageResponse)
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


@career_pages_router.delete("/career-pages/{page_id}", status_code=204, response_model=None)
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
