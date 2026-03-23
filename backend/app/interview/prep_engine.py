"""Contextual interview prep engine.

Generates stage-specific interview preparation material by combining
job description analysis, user resume, and company context.
"""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.enrichment.llm_client import LLMClient
from app.interview.models import InterviewPrepPackage
from app.interview.prompts import CONTEXTUAL_PREP_PROMPT
from app.interview.schemas import (
    VALID_PREP_STAGES,
    ContextualPrepData,
    ContextualPrepResponse,
)
from app.nlp.model_router import ModelRouter
from app.pipeline.models import Application
from app.shared.errors import AppError, NotFoundError, ValidationError

logger = structlog.get_logger()
_JSON_SYSTEM = {"role": "system", "content": "Return ONLY valid JSON."}


def _build_router() -> ModelRouter:
    llm = LLMClient(settings.openrouter_api_key, settings.default_llm_model)
    return ModelRouter(llm)


class InterviewPrepEngine:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._router = _build_router()

    async def generate_prep(
        self,
        application_id: uuid.UUID,
        user_id: uuid.UUID,
        stage: str = "general",
    ) -> InterviewPrepPackage:
        if stage not in VALID_PREP_STAGES:
            raise ValidationError(
                f"Invalid stage: {stage}. Must be one of {VALID_PREP_STAGES}"
            )

        app = await self._get_application(application_id, user_id)
        job_title, company_name, job_description, required_skills = (
            await self._load_job_context(app.job_id)
        )
        resume_text = await self._load_resume_text(user_id)

        # Use application-level overrides if job data is sparse
        job_title = job_title or app.position_title or ""
        company_name = company_name or app.company_name or ""

        prompt = CONTEXTUAL_PREP_PROMPT.format(
            stage=stage,
            job_title=job_title,
            company_name=company_name or "the company",
            job_description=(job_description or "Not available")[:3000],
            required_skills=required_skills or "Not specified",
            resume_text=(resume_text or "Not provided")[:4000],
        )
        messages = [_JSON_SYSTEM, {"role": "user", "content": prompt}]

        try:
            data = await self._router.complete_json(
                task="interview",
                messages=messages,
                temperature=0.3,
                max_tokens=3000,
            )
        except RuntimeError as exc:
            logger.exception(
                "interview.contextual_prep_failed",
                application_id=str(application_id),
            )
            raise AppError("Interview prep generation failed", status_code=502) from exc

        if not data:
            raise AppError("Interview prep generation returned empty result", status_code=502)

        # Validate the data parses correctly
        prep_data = ContextualPrepData(
            company_research=data.get("company_research", {}),
            role_analysis=data.get("role_analysis", {}),
            likely_questions=data.get("likely_questions", []),
            suggested_answers=data.get("suggested_answers", []),
            questions_to_ask=data.get("questions_to_ask", []),
            red_flags=data.get("red_flags", []),
        )

        # Persist the package
        package = InterviewPrepPackage(
            application_id=application_id,
            user_id=user_id,
            stage=stage,
            prep_data=prep_data.model_dump(),
        )
        self.db.add(package)
        await self.db.commit()
        await self.db.refresh(package)

        logger.info(
            "interview.contextual_prep_generated",
            application_id=str(application_id),
            stage=stage,
            questions=len(prep_data.likely_questions),
        )
        return package

    async def get_prep(
        self,
        application_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> InterviewPrepPackage:
        result = await self.db.execute(
            select(InterviewPrepPackage)
            .where(
                InterviewPrepPackage.application_id == application_id,
                InterviewPrepPackage.user_id == user_id,
            )
            .order_by(InterviewPrepPackage.updated_at.desc())
            .limit(1)
        )
        package = result.scalar_one_or_none()
        if package is None:
            raise NotFoundError(
                f"No interview prep found for application {application_id}"
            )
        return package

    async def _get_application(
        self, application_id: uuid.UUID, user_id: uuid.UUID
    ) -> Application:
        result = await self.db.execute(
            select(Application).where(
                Application.id == application_id,
                Application.user_id == user_id,
            )
        )
        app = result.scalar_one_or_none()
        if app is None:
            raise NotFoundError(f"Application {application_id} not found")
        return app

    async def _load_job_context(
        self, job_id: str | None
    ) -> tuple[str, str, str, str]:
        if not job_id:
            return "", "", "", ""
        try:
            from app.jobs.models import Job

            job = await self.db.scalar(select(Job).where(Job.id == job_id))
            if job is None:
                return "", "", "", ""
            description = (
                getattr(job, "description_clean", "") or getattr(job, "description", "") or ""
            )
            required_skills = getattr(job, "required_skills", None)
            if isinstance(required_skills, list):
                skills_str = ", ".join(required_skills)
            elif isinstance(required_skills, str):
                skills_str = required_skills
            else:
                skills_str = ""
            return (
                getattr(job, "title", "") or "",
                getattr(job, "company_name", "") or "",
                description,
                skills_str,
            )
        except Exception:
            logger.debug("interview.load_job_context_failed", job_id=job_id)
            return "", "", "", ""

    async def _load_resume_text(self, user_id: uuid.UUID) -> str:
        try:
            from app.resume.models import ResumeVersion

            result = await self.db.execute(
                select(ResumeVersion)
                .where(ResumeVersion.user_id == user_id)
                .order_by(ResumeVersion.created_at.desc())
                .limit(1)
            )
            resume = result.scalar_one_or_none()
            if resume is None:
                return ""
            return getattr(resume, "parsed_text", "") or ""
        except Exception:
            logger.debug("interview.load_resume_failed", user_id=str(user_id))
            return ""


def to_prep_response(package: InterviewPrepPackage) -> ContextualPrepResponse:
    prep_data = package.prep_data
    if isinstance(prep_data, dict):
        prep_data = ContextualPrepData(**prep_data)
    return ContextualPrepResponse(
        id=package.id,
        application_id=package.application_id,
        stage=package.stage,
        prep_data=prep_data,
        created_at=package.created_at,
        updated_at=package.updated_at,
    )
