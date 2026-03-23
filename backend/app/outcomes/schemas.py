from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

# ── Request schemas ─────────────────────────────────────────────


class OutcomeCreate(BaseModel):
    rejection_reason: str | None = None
    rejection_stage: str | None = None
    days_to_response: int | None = None
    offer_amount: int | None = None
    offer_equity: str | None = None
    offer_total_comp: int | None = None
    negotiated_amount: int | None = None
    final_decision: str | None = None
    was_ghosted: bool = False
    referral_used: bool = False
    cover_letter_used: bool = False
    application_method: str | None = None
    feedback_notes: str | None = None
    stage_reached: str | None = None


class OutcomeUpdate(BaseModel):
    rejection_reason: str | None = None
    rejection_stage: str | None = None
    days_to_response: int | None = None
    offer_amount: int | None = None
    offer_equity: str | None = None
    offer_total_comp: int | None = None
    negotiated_amount: int | None = None
    final_decision: str | None = None
    was_ghosted: bool | None = None
    referral_used: bool | None = None
    cover_letter_used: bool | None = None
    application_method: str | None = None
    feedback_notes: str | None = None
    stage_reached: str | None = None


# ── Response schemas ────────────────────────────────────────────


class OutcomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    user_id: uuid.UUID
    stage_reached: str | None = None
    rejection_reason: str | None = None
    rejection_stage: str | None = None
    days_to_response: int | None = None
    offer_amount: int | None = None
    offer_equity: str | None = None
    offer_total_comp: int | None = None
    negotiated_amount: int | None = None
    final_decision: str | None = None
    was_ghosted: bool = False
    referral_used: bool = False
    cover_letter_used: bool = False
    application_method: str | None = None
    feedback_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class CompanyInsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_name: str
    total_applications: int = 0
    callback_count: int = 0
    avg_response_days: float | None = None
    ghosted_count: int = 0
    ghost_rate: float = 0.0
    rejection_rate: float = 0.0
    offer_rate: float = 0.0
    offers_received: int = 0
    avg_offer_amount: float | None = None
    interview_difficulty: float | None = None
    culture_notes: str | None = None
    last_applied_at: datetime | None = None


class UserOutcomeStats(BaseModel):
    total_applications: int = 0
    total_outcomes: int = 0
    avg_days_to_response: float | None = None
    ghosting_rate: float = 0.0
    response_rate: float = 0.0
    offer_rate: float = 0.0
    avg_offer_amount: float | None = None
    top_rejection_reasons: list[RejectionReasonCount] = []
    stage_distribution: dict[str, int] = {}


class RejectionReasonCount(BaseModel):
    reason: str
    count: int


# Rebuild UserOutcomeStats since it references RejectionReasonCount
UserOutcomeStats.model_rebuild()
