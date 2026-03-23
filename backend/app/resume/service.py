"""Resume service — thin orchestration layer.

Delegates to ``prompts``, ``gap_analyzer``, and ``council`` submodules.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.enrichment.llm_client import LLMClient
from app.jobs.models import Job
from app.nlp.model_router import ModelRouter
from app.resume.council import council_evaluate as _council_evaluate
from app.resume.gap_analyzer import run_gap_analysis
from app.resume.models import ResumeVersion
from app.resume.prompts import STAGE1_PROMPT, STAGE2_PROMPT, STAGE3_PROMPT
from app.resume.schemas import (
    VALID_TONES,
    CouncilRequest,
    CoverLetterGenerateRequest,
    GapAnalysisRequest,
    ResumeTailorRequest,
)
from app.shared.errors import NotFoundError

logger = structlog.get_logger()


class ResumeService:
    """Resume tailoring, gap analysis, and multi-model council evaluation."""

    def __init__(self, db: AsyncSession, llm_client: LLMClient | None = None) -> None:
        self.db = db
        self._llm = llm_client or LLMClient(
            api_key=settings.openrouter_api_key,
            model=settings.default_llm_model,
        )
        self._router = ModelRouter(self._llm)

    # -- DB helpers --------------------------------------------------------

    async def _get_resume(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> ResumeVersion:
        q = select(ResumeVersion).where(
            ResumeVersion.id == resume_id, ResumeVersion.user_id == user_id
        )
        version = await self.db.scalar(q)
        if version is None:
            raise NotFoundError(detail=f"Resume version {resume_id} not found")
        return version

    async def _get_default_resume(self, user_id: uuid.UUID) -> ResumeVersion:
        q = (
            select(ResumeVersion)
            .where(ResumeVersion.user_id == user_id)
            .order_by(ResumeVersion.is_default.desc(), ResumeVersion.created_at.desc())
            .limit(1)
        )
        version = await self.db.scalar(q)
        if version is None:
            raise NotFoundError(detail="No resume found for user")
        return version

    async def _get_job(self, job_id: str, user_id: uuid.UUID) -> Job:
        job = await self.db.scalar(select(Job).where(Job.id == job_id, Job.user_id == user_id))
        if job is None:
            raise NotFoundError(detail=f"Job {job_id} not found")
        return job

    def _resume_as_parsed(self, version: ResumeVersion) -> dict:
        structured = version.parsed_structured or {}
        return {
            "text": version.parsed_text or "",
            "skills": structured.get("skills", []),
            "sections": structured.get("sections", {}),
        }

    def _job_as_dict(self, job: Job) -> dict:
        return {
            "title": job.title,
            "description_clean": job.description_clean or "",
            "skills_required": job.skills_required or [],
            "skills_nice_to_have": job.skills_nice_to_have or [],
            "tech_stack": job.tech_stack or [],
        }

    # -- CRUD --------------------------------------------------------------

    async def list_versions(self, user_id: uuid.UUID) -> list[ResumeVersion]:
        logger.info("resume.list_versions", user_id=str(user_id))
        q = (
            select(ResumeVersion)
            .where(ResumeVersion.user_id == user_id)
            .order_by(ResumeVersion.created_at.desc())
        )
        return list((await self.db.scalars(q)).all())

    async def get_version(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> ResumeVersion:
        logger.info("resume.get_version", resume_id=str(resume_id), user_id=str(user_id))
        return await self._get_resume(resume_id, user_id)

    async def upload_resume(
        self, filename: str, content: bytes, user_id: uuid.UUID
    ) -> ResumeVersion:
        logger.info("resume.upload_resume", filename=filename, user_id=str(user_id))
        version = ResumeVersion(
            user_id=user_id, filename=filename, parsed_text=content.decode(errors="replace")
        )
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)
        return version

    # -- 3-stage tailoring -------------------------------------------------

    async def tailor_resume(
        self, request: ResumeTailorRequest, user_id: uuid.UUID
    ) -> dict[str, Any]:
        """Run the 3-stage LLM tailoring pipeline."""
        logger.info("resume.tailor_resume", job_id=request.job_id, user_id=str(user_id))

        if request.resume_version_id:
            version = await self._get_resume(request.resume_version_id, user_id)
        else:
            version = await self._get_default_resume(user_id)

        job_dict = self._job_as_dict(await self._get_job(request.job_id, user_id))
        resume_text = (version.parsed_text or "").strip()
        if not resume_text:
            raise ValueError("Resume text is required for tailoring")

        s1 = await self._llm_stage(
            STAGE1_PROMPT.format(
                job_title=job_dict.get("title", ""),
                job_description=(job_dict.get("description_clean", "") or "")[:3000],
            ),
            system="Return ONLY valid JSON.",
            stage_label="stage1",
        )

        s2 = await self._llm_stage(
            STAGE2_PROMPT.format(
                resume_text=resume_text[:4000],
                hard_requirements=", ".join(s1.get("hard_requirements", [])),
                soft_requirements=", ".join(s1.get("soft_requirements", [])),
                key_technologies=", ".join(s1.get("key_technologies", [])),
                ats_keywords=", ".join(s1.get("ats_keywords", [])),
            ),
            system="Return ONLY valid JSON.",
            stage_label="stage2",
        )

        partial = s2.get("partial_matches", [])
        partial_strs = [
            f"{p.get('requirement', '')}: {p.get('gap', '')}"
            for p in partial
            if isinstance(p, dict)
        ]
        s3 = await self._llm_stage(
            STAGE3_PROMPT.format(
                resume_text=resume_text[:4000],
                missing_keywords=", ".join(s2.get("keyword_coverage", {}).get("missing", [])),
                matched_requirements=", ".join(s2.get("matched_requirements", [])),
                partial_matches="; ".join(partial_strs) if partial_strs else "None",
            ),
            system="Return ONLY valid JSON. Never fabricate experience.",
            stage_label="stage3",
            temperature=0.2,
            max_tokens=2000,
        )

        return {
            "summary": s3.get("summary", ""),
            "reordered_experience": s3.get("reordered_experience", []),
            "enhanced_bullets": s3.get("enhanced_bullets", []),
            "skills_section": s3.get("skills_section", []),
            "ats_score_before": int(s3.get("ats_score_before", 0)),
            "ats_score_after": int(s3.get("ats_score_after", 0)),
            "stage1_output": s1,
            "stage2_output": s2,
        }

    async def _llm_stage(
        self,
        user_prompt: str,
        *,
        system: str,
        stage_label: str,
        temperature: float = 0.1,
        max_tokens: int = 1500,
    ) -> dict[str, Any]:
        try:
            result = await self._router.complete_json(
                task="resume_tailor",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            logger.error(f"resume.tailor.{stage_label}_failed", error=str(exc))
            raise RuntimeError(f"Stage ({stage_label}) failed: {exc}") from exc
        logger.info(f"resume.tailor.{stage_label}_complete")
        return result

    # -- Gap analysis ------------------------------------------------------

    async def analyze_gaps(
        self, request: GapAnalysisRequest, user_id: uuid.UUID
    ) -> dict[str, Any]:
        logger.info(
            "resume.analyze_gaps",
            resume_version_id=str(request.resume_version_id),
            job_id=request.job_id,
            user_id=str(user_id),
        )
        version = await self._get_resume(request.resume_version_id, user_id)
        job = await self._get_job(request.job_id, user_id)
        return run_gap_analysis(self._resume_as_parsed(version), self._job_as_dict(job))

    # -- Council evaluation ------------------------------------------------

    async def council_evaluate(
        self, request: CouncilRequest, user_id: uuid.UUID
    ) -> dict[str, Any]:
        logger.info(
            "resume.council_evaluate",
            resume_version_id=str(request.resume_version_id),
            user_id=str(user_id),
        )
        version = await self._get_resume(request.resume_version_id, user_id)
        resume_text = (version.parsed_text or "").strip()
        if not resume_text:
            raise ValueError("Resume text is required for council evaluation")

        job_title, job_description = "", ""
        if request.job_id:
            job = await self._get_job(request.job_id, user_id)
            job_title = job.title
            job_description = (job.description_clean or "")[:3000]

        return await _council_evaluate(
            resume_text=resume_text,
            job_title=job_title,
            job_description=job_description,
            llm_client=self._llm,
        )

    # -- Cover letter generation (B6) --------------------------------------

    async def generate_cover_letter(
        self, request: CoverLetterGenerateRequest, user_id: uuid.UUID
    ) -> dict[str, Any]:
        from app.companies.models import Company
        from app.nlp.cover_letter import generate_cover_letter as _generate_cl

        tone = request.tone
        if tone not in VALID_TONES:
            raise ValueError(
                f"Invalid tone {tone!r}. Must be one of: {sorted(VALID_TONES)}"
            )

        # Map B6 tones to existing cover_letter.py styles
        tone_to_style = {
            "formal": "professional",
            "conversational": "conversational",
            "enthusiastic": "storytelling",
        }
        style = tone_to_style[tone]

        if request.resume_version_id:
            version = await self._get_resume(request.resume_version_id, user_id)
        else:
            version = await self._get_default_resume(user_id)

        job = await self._get_job(request.job_id, user_id)
        resume_parsed = self._resume_as_parsed(version)

        # Build company context from DB (B6 enhancement)
        company_context = ""
        company_context_used = False
        if job.company_name:
            company = await self.db.scalar(
                select(Company).where(
                    Company.canonical_name.ilike(job.company_name)
                )
            )
            if company:
                company_context_used = True
                parts = [f"Company: {company.canonical_name}"]
                if company.domain:
                    parts.append(f"Domain: {company.domain}")
                if company.ats_provider:
                    parts.append(f"ATS: {company.ats_provider}")
                company_context = "\n".join(parts)

        job_data = self._job_as_dict(job)
        job_data["company_name"] = job.company_name or "the company"
        job_data["company_context"] = company_context

        result = await _generate_cl(
            resume_parsed=resume_parsed,
            job_data=job_data,
            style=style,
            template=request.template,
        )

        return {
            "content": result.content,
            "key_points_addressed": result.key_points_addressed,
            "skills_highlighted": result.skills_highlighted,
            "company_research_notes": result.company_research_notes,
            "word_count": result.word_count,
            "reading_level": result.reading_level,
            "tone_used": tone,
            "company_context_used": company_context_used,
        }
