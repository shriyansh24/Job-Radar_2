from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.copilot.models import CoverLetter
from app.resume.models import ResumeVersion
from app.shared.errors import NotFoundError

logger = structlog.get_logger()


class VaultService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_resumes(self, user_id: uuid.UUID) -> list[ResumeVersion]:
        """Return all resume versions for the given user."""
        logger.info("vault.list_resumes", user_id=str(user_id))
        query = select(ResumeVersion).where(ResumeVersion.user_id == user_id)
        result = await self.db.scalars(query)
        return list(result.all())

    async def list_cover_letters(self, user_id: uuid.UUID) -> list[CoverLetter]:
        """Return all cover letters for the given user."""
        logger.info("vault.list_cover_letters", user_id=str(user_id))
        query = select(CoverLetter).where(CoverLetter.user_id == user_id)
        result = await self.db.scalars(query)
        return list(result.all())

    async def update_resume(
        self,
        resume_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        label: str | None = None,
    ) -> ResumeVersion:
        """Update mutable resume metadata owned by the user."""
        logger.info(
            "vault.update_resume",
            resume_id=str(resume_id),
            user_id=str(user_id),
        )
        query = select(ResumeVersion).where(
            ResumeVersion.id == resume_id,
            ResumeVersion.user_id == user_id,
        )
        resume = await self.db.scalar(query)
        if resume is None:
            raise NotFoundError(detail=f"Resume {resume_id} not found")

        resume.label = label or None
        await self.db.commit()
        await self.db.refresh(resume)
        return resume

    async def update_cover_letter(
        self,
        letter_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        content: str | None = None,
    ) -> CoverLetter:
        """Update the saved cover-letter content for the given user."""
        logger.info(
            "vault.update_cover_letter",
            letter_id=str(letter_id),
            user_id=str(user_id),
        )
        query = select(CoverLetter).where(
            CoverLetter.id == letter_id,
            CoverLetter.user_id == user_id,
        )
        letter = await self.db.scalar(query)
        if letter is None:
            raise NotFoundError(detail=f"Cover letter {letter_id} not found")

        if content is not None:
            letter.content = content

        await self.db.commit()
        await self.db.refresh(letter)
        return letter

    async def delete_resume(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a resume version owned by the user."""
        logger.info(
            "vault.delete_resume",
            resume_id=str(resume_id),
            user_id=str(user_id),
        )
        query = select(ResumeVersion).where(
            ResumeVersion.id == resume_id,
            ResumeVersion.user_id == user_id,
        )
        resume = await self.db.scalar(query)
        if resume is None:
            raise NotFoundError(detail=f"Resume {resume_id} not found")
        await self.db.delete(resume)
        await self.db.commit()

    async def delete_cover_letter(self, letter_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a cover letter owned by the user."""
        logger.info(
            "vault.delete_cover_letter",
            letter_id=str(letter_id),
            user_id=str(user_id),
        )
        query = select(CoverLetter).where(
            CoverLetter.id == letter_id,
            CoverLetter.user_id == user_id,
        )
        letter = await self.db.scalar(query)
        if letter is None:
            raise NotFoundError(detail=f"Cover letter {letter_id} not found")
        await self.db.delete(letter)
        await self.db.commit()
