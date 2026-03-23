from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Contact schemas
# ---------------------------------------------------------------------------


class ContactCreate(BaseModel):
    name: str
    company: str | None = None
    role: str | None = None
    relationship_strength: int = 3
    linkedin_url: str | None = None
    email: str | None = None
    notes: str | None = None


class ContactUpdate(BaseModel):
    name: str | None = None
    company: str | None = None
    role: str | None = None
    relationship_strength: int | None = None
    linkedin_url: str | None = None
    email: str | None = None
    notes: str | None = None


class ContactResponse(BaseModel):
    id: uuid.UUID
    name: str
    company: str | None = None
    role: str | None = None
    relationship_strength: int = 3
    linkedin_url: str | None = None
    email: str | None = None
    last_contacted: datetime | None = None
    notes: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Referral schemas
# ---------------------------------------------------------------------------


class ReferralSuggestion(BaseModel):
    contact: ContactResponse
    relevance_reason: str
    suggested_message: str = ""


class ReferralRequestCreate(BaseModel):
    contact_id: uuid.UUID
    job_id: str
    message_template: str | None = None


class ReferralRequestResponse(BaseModel):
    id: uuid.UUID
    contact_id: uuid.UUID
    job_id: str
    status: str = "draft"
    message_template: str | None = None
    sent_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class OutreachRequest(BaseModel):
    contact_id: uuid.UUID
    job_id: str
