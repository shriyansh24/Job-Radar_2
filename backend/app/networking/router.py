from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.networking.schemas import (
    ContactCreate,
    ContactResponse,
    ContactUpdate,
    OutreachRequest,
    ReferralRequestCreate,
    ReferralRequestResponse,
    ReferralSuggestion,
)
from app.networking.service import NetworkingService

router = APIRouter(prefix="/networking", tags=["networking"])


# ---------------------------------------------------------------------------
# Contact CRUD
# ---------------------------------------------------------------------------


@router.post("/contacts", response_model=ContactResponse, status_code=201)
async def create_contact(
    data: ContactCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContactResponse:
    svc = NetworkingService(db)
    contact = await svc.create_contact(data, user.id)
    return ContactResponse.model_validate(contact)


@router.get("/contacts", response_model=list[ContactResponse])
async def list_contacts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContactResponse]:
    svc = NetworkingService(db)
    contacts = await svc.list_contacts(user.id)
    return [ContactResponse.model_validate(c) for c in contacts]


@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContactResponse:
    svc = NetworkingService(db)
    contact = await svc.get_contact(contact_id, user.id)
    return ContactResponse.model_validate(contact)


@router.patch("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: uuid.UUID,
    data: ContactUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContactResponse:
    svc = NetworkingService(db)
    contact = await svc.update_contact(contact_id, data, user.id)
    return ContactResponse.model_validate(contact)


@router.delete("/contacts/{contact_id}", status_code=204, response_model=None)
async def delete_contact(
    contact_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = NetworkingService(db)
    await svc.delete_contact(contact_id, user.id)


# ---------------------------------------------------------------------------
# Connection search & referral suggestions
# ---------------------------------------------------------------------------


@router.get("/connections/{company}", response_model=list[ContactResponse])
async def find_connections(
    company: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContactResponse]:
    svc = NetworkingService(db)
    contacts = await svc.find_connections(user.id, company)
    return [ContactResponse.model_validate(c) for c in contacts]


@router.get("/referral-suggestions/{job_id}", response_model=list[ReferralSuggestion])
async def suggest_referral(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ReferralSuggestion]:
    svc = NetworkingService(db)
    return await svc.suggest_referral(user.id, job_id)


# ---------------------------------------------------------------------------
# Outreach generation
# ---------------------------------------------------------------------------


@router.post("/outreach")
async def generate_outreach(
    data: OutreachRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    svc = NetworkingService(db)
    message = await svc.generate_outreach(data.contact_id, data.job_id, user.id)
    return {"message": message}


# ---------------------------------------------------------------------------
# Referral requests
# ---------------------------------------------------------------------------


@router.post("/referral-requests", response_model=ReferralRequestResponse, status_code=201)
async def create_referral_request(
    data: ReferralRequestCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReferralRequestResponse:
    svc = NetworkingService(db)
    rr = await svc.create_referral_request(data, user.id)
    return ReferralRequestResponse.model_validate(rr)


@router.get("/referral-requests", response_model=list[ReferralRequestResponse])
async def list_referral_requests(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ReferralRequestResponse]:
    svc = NetworkingService(db)
    requests = await svc.list_referral_requests(user.id)
    return [ReferralRequestResponse.model_validate(r) for r in requests]
