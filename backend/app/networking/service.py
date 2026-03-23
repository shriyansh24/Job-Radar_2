from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.enrichment.llm_client import LLMClient
from app.networking.models import Contact, ReferralRequest
from app.networking.schemas import (
    ContactCreate,
    ContactResponse,
    ContactUpdate,
    ReferralRequestCreate,
    ReferralSuggestion,
)
from app.nlp.model_router import ModelRouter
from app.shared.errors import AppError, NotFoundError

logger = structlog.get_logger()

_OUTREACH_PROMPT = """You are a networking coach. Generate a professional outreach message.

SENDER CONTEXT: A job seeker reaching out to a contact for a potential referral.

CONTACT NAME: {contact_name}
CONTACT ROLE: {contact_role}
CONTACT COMPANY: {contact_company}
RELATIONSHIP STRENGTH: {relationship_strength}/5

TARGET JOB TITLE: {job_title}
TARGET COMPANY: {target_company}
JOB DESCRIPTION SUMMARY: {job_summary}

Write a concise, professional outreach message (3-5 sentences) that:
1. References the relationship naturally
2. Mentions the specific role
3. Asks for a referral or introduction politely
4. Feels authentic, not templated

Return ONLY the message text, no JSON wrapping.
"""


def _build_router() -> ModelRouter:
    llm = LLMClient(settings.openrouter_api_key, settings.default_llm_model)
    return ModelRouter(llm)


class NetworkingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Contact CRUD
    # ------------------------------------------------------------------

    async def create_contact(
        self, data: ContactCreate, user_id: uuid.UUID
    ) -> Contact:
        contact = Contact(user_id=user_id, **data.model_dump())
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def list_contacts(self, user_id: uuid.UUID) -> list[Contact]:
        result = await self.db.execute(
            select(Contact)
            .where(Contact.user_id == user_id)
            .order_by(Contact.name)
        )
        return list(result.scalars().all())

    async def get_contact(
        self, contact_id: uuid.UUID, user_id: uuid.UUID
    ) -> Contact:
        contact = await self.db.scalar(
            select(Contact).where(
                Contact.id == contact_id, Contact.user_id == user_id
            )
        )
        if contact is None:
            raise NotFoundError("Contact not found")
        return contact

    async def update_contact(
        self,
        contact_id: uuid.UUID,
        data: ContactUpdate,
        user_id: uuid.UUID,
    ) -> Contact:
        contact = await self.get_contact(contact_id, user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(contact, field, value)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def delete_contact(
        self, contact_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        contact = await self.get_contact(contact_id, user_id)
        await self.db.delete(contact)
        await self.db.commit()

    # ------------------------------------------------------------------
    # Connection search
    # ------------------------------------------------------------------

    async def find_connections(
        self, user_id: uuid.UUID, company: str
    ) -> list[Contact]:
        result = await self.db.execute(
            select(Contact)
            .where(
                Contact.user_id == user_id,
                Contact.company.ilike(f"%{company}%"),
            )
            .order_by(Contact.relationship_strength.desc())
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Referral suggestion
    # ------------------------------------------------------------------

    async def suggest_referral(
        self, user_id: uuid.UUID, job_id: str
    ) -> list[ReferralSuggestion]:
        from app.jobs.models import Job

        job = await self.db.scalar(select(Job).where(Job.id == job_id))
        if job is None:
            raise NotFoundError("Job not found")

        company_name = job.company_name or ""
        suggestions: list[ReferralSuggestion] = []

        # Find contacts at the same company
        if company_name:
            contacts = await self.find_connections(user_id, company_name)
            for contact in contacts:
                suggestions.append(
                    ReferralSuggestion(
                        contact=ContactResponse.model_validate(contact),
                        relevance_reason=f"Works at {company_name}",
                    )
                )

        return suggestions

    # ------------------------------------------------------------------
    # LLM-generated outreach
    # ------------------------------------------------------------------

    async def generate_outreach(
        self,
        contact_id: uuid.UUID,
        job_id: str,
        user_id: uuid.UUID,
    ) -> str:
        from app.jobs.models import Job

        contact = await self.get_contact(contact_id, user_id)
        job = await self.db.scalar(select(Job).where(Job.id == job_id))
        if job is None:
            raise NotFoundError("Job not found")

        summary = (job.summary_ai or job.description_clean or "")[:500]

        prompt = _OUTREACH_PROMPT.format(
            contact_name=contact.name,
            contact_role=contact.role or "Unknown",
            contact_company=contact.company or "Unknown",
            relationship_strength=contact.relationship_strength,
            job_title=job.title or "Unknown",
            target_company=job.company_name or "Unknown",
            job_summary=summary or "Not available",
        )

        messages = [
            {
                "role": "system",
                "content": "Write a professional networking outreach message. "
                "Return only the message text.",
            },
            {"role": "user", "content": prompt},
        ]

        router = _build_router()
        try:
            result = await router.complete(
                task="default",
                messages=messages,
                temperature=0.4,
                max_tokens=500,
            )
        except RuntimeError:
            logger.exception("networking.outreach_llm_failed")
            raise AppError("Outreach generation failed", status_code=502)
        finally:
            await router._llm.close()

        return result

    # ------------------------------------------------------------------
    # Referral request CRUD
    # ------------------------------------------------------------------

    async def create_referral_request(
        self,
        data: ReferralRequestCreate,
        user_id: uuid.UUID,
    ) -> ReferralRequest:
        # Validate contact belongs to user
        await self.get_contact(data.contact_id, user_id)

        rr = ReferralRequest(user_id=user_id, **data.model_dump())
        self.db.add(rr)
        await self.db.commit()
        await self.db.refresh(rr)
        return rr

    async def list_referral_requests(
        self, user_id: uuid.UUID
    ) -> list[ReferralRequest]:
        result = await self.db.execute(
            select(ReferralRequest)
            .where(ReferralRequest.user_id == user_id)
            .order_by(ReferralRequest.created_at.desc())
        )
        return list(result.scalars().all())
