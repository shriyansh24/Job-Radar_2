from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.companies.schemas import CompanyResolveRequest, CompanyResponse
from app.companies.service import CompanyService
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyResponse])
async def list_companies(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CompanyResponse]:
    svc = CompanyService(db)
    items = await svc.list_companies()
    return [CompanyResponse.model_validate(c) for c in items]


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    svc = CompanyService(db)
    c = await svc.get_company(company_id)
    return CompanyResponse.model_validate(c)


@router.post("/resolve", response_model=CompanyResponse)
async def resolve_company(
    data: CompanyResolveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    svc = CompanyService(db)
    c = await svc.resolve_company(data.name)
    return CompanyResponse.model_validate(c)
