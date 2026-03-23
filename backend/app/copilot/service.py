"""Copilot service: streaming chat and cover letter generation.

Uses v2's LLMClient for streaming chat and delegates cover letter
generation to the nlp.cover_letter module.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.copilot.models import CoverLetter
from app.copilot.prompts import COPILOT_SYSTEM_PROMPT, build_context_messages
from app.enrichment.llm_client import LLMClient
from app.jobs.models import Job
from app.nlp.cover_letter import generate_cover_letter as _generate_cover_letter
from app.resume.models import ResumeVersion

logger = structlog.get_logger()


def _build_llm_client() -> LLMClient:
    """Create an LLMClient from app settings."""
    return LLMClient(
        api_key=settings.openrouter_api_key,
        model=settings.default_llm_model,
    )


class CopilotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------
    # Streaming chat
    # -----------------------------------------------------------------

    async def chat(
        self,
        message: str,
        context: dict | None,
        user_id: uuid.UUID,
    ) -> AsyncGenerator[str, None]:
        """Stream a copilot chat response using the LLM.

        Falls back to a static message when the LLM is not configured.
        """
        logger.info(
            "copilot_chat",
            user_id=str(user_id),
            message_length=len(message),
        )

        llm = _build_llm_client()

        if not llm.is_configured:
            logger.warning("copilot_llm_not_configured")
            yield "LLM is not configured. Please set your OpenRouter API key."
            return

        # Build message list
        messages: list[dict[str, str]] = [
            {"role": "system", "content": COPILOT_SYSTEM_PROMPT},
        ]
        messages.extend(build_context_messages(context))
        messages.append({"role": "user", "content": message})

        try:
            async for chunk in llm.chat_stream(
                messages=messages,
                temperature=0.4,
                max_tokens=2000,
                model=None,  # use the "copilot" task default via settings
            ):
                yield chunk
        except Exception as exc:
            logger.error("copilot_chat_failed", error=str(exc))
            # Fixed: CodeQL py/stack-trace-exposure
            yield "Sorry, I encountered an error. Please try again later."
        finally:
            await llm.close()

    # -----------------------------------------------------------------
    # Cover letter generation
    # -----------------------------------------------------------------

    async def generate_cover_letter(
        self,
        job_id: str,
        style: str,
        user_id: uuid.UUID,
        template: Optional[str] = None,
    ) -> CoverLetter:
        """Generate a cover letter for a job using LLM and persist it.

        Fetches the job and the user's default resume from the DB, then
        delegates to ``nlp.cover_letter.generate_cover_letter``.
        Falls back to a placeholder when the LLM is not configured.
        """
        logger.info(
            "cover_letter_request",
            user_id=str(user_id),
            job_id=job_id,
            style=style,
            template=template,
        )

        # Fetch the job
        result = await self.db.execute(select(Job).where(Job.id == job_id, Job.user_id == user_id))
        job = result.scalar_one_or_none()

        # Fetch the user's default resume (or most recent)
        resume_result = await self.db.execute(
            select(ResumeVersion)
            .where(ResumeVersion.user_id == user_id)
            .order_by(ResumeVersion.is_default.desc(), ResumeVersion.created_at.desc())
            .limit(1)
        )
        resume = resume_result.scalar_one_or_none()

        # Build dicts expected by the cover letter generator
        job_data: dict = {}
        if job:
            job_data = {
                "title": job.title or "",
                "company_name": job.company_name or "the company",
                "description_clean": job.description_clean or job.description_raw or "",
                "skills_required": job.skills_required or [],
            }
        else:
            logger.warning("cover_letter_job_not_found", job_id=job_id)

        resume_parsed: dict = {"text": "", "skills": [], "sections": {}}
        if resume:
            resume_parsed["text"] = resume.parsed_text or ""
            if resume.parsed_structured:
                resume_parsed["skills"] = resume.parsed_structured.get("skills", [])
                resume_parsed["sections"] = resume.parsed_structured.get("sections", {})

        # Generate via LLM
        content = "Cover letter generation failed -- LLM not configured or no resume found."
        if settings.openrouter_api_key and resume_parsed.get("text"):
            try:
                cl_result = await _generate_cover_letter(
                    resume_parsed=resume_parsed,
                    job_data=job_data,
                    style=style,
                    template=template,
                )
                content = cl_result.content
            except Exception as exc:
                logger.error("cover_letter_llm_failed", error=str(exc))
                # Fixed: CodeQL py/stack-trace-exposure
                content = "Cover letter generation encountered an error. Please try again later."
        elif not settings.openrouter_api_key:
            content = "Cover letter generation requires an OpenRouter API key to be configured."
        elif not resume_parsed.get("text"):
            content = "Please upload a resume before generating a cover letter."

        # Persist
        cover_letter = CoverLetter(
            user_id=user_id,
            job_id=job_id,
            style=style,
            content=content,
        )
        self.db.add(cover_letter)
        await self.db.commit()
        await self.db.refresh(cover_letter)

        logger.info(
            "cover_letter_generated",
            cover_letter_id=str(cover_letter.id),
            user_id=str(user_id),
            job_id=job_id,
            style=style,
        )
        return cover_letter
