"""4-stage resume tailoring engine with user review.

Stage 1: Analyze job requirements (must-haves, nice-to-haves, keywords)
Stage 2: Match resume sections to job requirements
Stage 3: Generate tailored resume proposal (diff for user review)
Stage 4: Apply approved changes to produce final ResumeIR
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enrichment.llm_client import LLMClient
from app.resume.models import ResumeVersion, TailoringSession
from app.resume.prompts import STAGE4_APPLY_PROMPT
from app.shared.errors import NotFoundError, ValidationError

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Prompt templates for proposal-oriented Stages 1-3
# ---------------------------------------------------------------------------

STAGE1_ANALYZE_PROMPT = """\
Analyze this job description and extract structured requirements.

JOB TITLE: {job_title}
JOB DESCRIPTION:
{job_description}

Return ONLY valid JSON:
{{
  "must_haves": ["requirement1", "requirement2"],
  "nice_to_haves": ["pref1", "pref2"],
  "keywords": ["keyword1", "keyword2"],
  "technologies": ["tech1", "tech2"],
  "seniority_level": "junior|mid|senior|staff",
  "culture_signals": ["signal1"]
}}
"""

STAGE2_MATCH_PROMPT = """\
Compare this resume to the job requirements and produce a match analysis.

RESUME (IR JSON):
{resume_ir}

JOB REQUIREMENTS (from Stage 1):
{stage1_result}

Return ONLY valid JSON:
{{
  "matched": ["requirement matched by resume evidence"],
  "partial": [{{"requirement": "...", "evidence": "...", "gap": "..."}}],
  "missing": ["requirement not found in resume"],
  "keyword_coverage": {{"present": ["kw1"], "missing": ["kw2"]}},
  "strongest_sections": ["section that helps most"],
  "weakest_sections": ["section that needs work"]
}}
"""

STAGE3_PROPOSE_PROMPT = """\
Based on the resume and job-requirement match analysis, generate specific \
change proposals. Each proposal modifies a single element of the resume.

RESUME (IR JSON):
{resume_ir}

MATCH ANALYSIS (from Stage 2):
{stage2_result}

JOB ANALYSIS (from Stage 1):
{stage1_result}

Generate a list of concrete proposals. Each must have:
- id (sequential integer starting at 0)
- type: one of "rewrite_bullet", "add_bullet", "remove_bullet", \
"add_skill", "reorder_section", "rewrite_summary"
- section: path like "work[0].bullets[2]", "skills", "summary"
- original: the original text (null for add operations)
- proposed: the new text
- reason: why this change helps (reference a specific JD requirement)
- confidence: 0.0-1.0 how certain this helps
- source: "jd_keyword" | "resume_existing" | "inferred"

Return ONLY valid JSON:
{{
  "proposals": [
    {{
      "id": 0,
      "type": "rewrite_bullet",
      "section": "work[0].bullets[0]",
      "original": "...",
      "proposed": "...",
      "reason": "...",
      "confidence": 0.85,
      "source": "jd_keyword"
    }}
  ]
}}
"""


class TailoringEngine:
    """Orchestrates the 4-stage tailoring pipeline with user review."""

    def __init__(self, db: AsyncSession, llm_client: LLMClient) -> None:
        self._db = db
        self._llm = llm_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start(
        self,
        resume_version_id: uuid.UUID,
        job_id: str,
        user_id: uuid.UUID,
    ) -> TailoringSession:
        """Run stages 1-3 and return a session with proposals for review."""
        resume = await self._get_resume(resume_version_id, user_id)
        ir_json = resume.ir_json or {}

        job = await self._get_job(job_id)

        job_title = getattr(job, "title", "") or ""
        job_desc = (getattr(job, "description_clean", "") or "")[:3000]

        # Stage 1: Analyze JD
        stage1 = await self._llm_json(
            STAGE1_ANALYZE_PROMPT.format(job_title=job_title, job_description=job_desc),
            stage="stage1",
        )

        # Stage 2: Match resume to JD
        stage2 = await self._llm_json(
            STAGE2_MATCH_PROMPT.format(
                resume_ir=json.dumps(ir_json, default=str),
                stage1_result=json.dumps(stage1, default=str),
            ),
            stage="stage2",
        )

        # Stage 3: Generate proposals (NOT auto-applied)
        stage3 = await self._llm_json(
            STAGE3_PROPOSE_PROMPT.format(
                resume_ir=json.dumps(ir_json, default=str),
                stage2_result=json.dumps(stage2, default=str),
                stage1_result=json.dumps(stage1, default=str),
            ),
            stage="stage3",
        )

        proposals = stage3.get("proposals", [])

        session = TailoringSession(
            resume_version_id=resume_version_id,
            job_id=job_id,
            user_id=user_id,
            status="proposals_ready",
            stage1_result=stage1,
            stage2_result=stage2,
            proposals=proposals,
        )
        self._db.add(session)
        await self._db.commit()
        await self._db.refresh(session)
        return session

    async def approve(
        self,
        session_id: uuid.UUID,
        approvals: list[bool],
        user_id: uuid.UUID,
    ) -> TailoringSession:
        """Apply approved proposals (stage 4) and produce a tailored IR."""
        session = await self._get_session(session_id, user_id)

        if session.status != "proposals_ready":
            raise ValidationError(
                f"Session status is '{session.status}', expected 'proposals_ready'"
            )

        proposals = session.proposals or []
        if len(approvals) != len(proposals):
            raise ValidationError(
                f"Approvals length ({len(approvals)}) must match proposals ({len(proposals)})"
            )

        approved_proposals = [p for p, a in zip(proposals, approvals) if a]

        # Get original IR
        resume = await self._get_resume(session.resume_version_id, session.user_id)
        original_ir = resume.ir_json or {}

        if not approved_proposals:
            # No changes approved — keep original
            tailored_ir = original_ir
        else:
            # Stage 4: Apply approved changes via LLM
            tailored_ir = await self._llm_json(
                STAGE4_APPLY_PROMPT.format(
                    original_ir=json.dumps(original_ir, default=str),
                    approved_changes=json.dumps(approved_proposals, default=str),
                ),
                stage="stage4",
            )

        # Create new ResumeVersion for tailored result
        new_version = ResumeVersion(
            user_id=session.user_id,
            filename=f"tailored_{session.job_id[:8]}.json",
            ir_json=tailored_ir,
            parsed_text=self._ir_to_text(tailored_ir),
            is_default=False,
            label=f"Tailored for {session.job_id[:8]}",
        )
        self._db.add(new_version)
        await self._db.flush()

        session.approvals = approvals
        session.tailored_ir = tailored_ir
        session.tailored_version_id = new_version.id
        session.status = "approved"
        await self._db.commit()
        await self._db.refresh(session)
        return session

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_resume(
        self, resume_id: uuid.UUID, user_id: uuid.UUID
    ) -> ResumeVersion:
        q = select(ResumeVersion).where(
            ResumeVersion.id == resume_id, ResumeVersion.user_id == user_id
        )
        version = await self._db.scalar(q)
        if version is None:
            raise NotFoundError(detail=f"Resume version {resume_id} not found")
        return version

    async def _get_job(self, job_id: str) -> Any:
        from app.jobs.models import Job

        job = await self._db.scalar(select(Job).where(Job.id == job_id))
        if job is None:
            raise NotFoundError(detail=f"Job {job_id} not found")
        return job

    async def _get_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> TailoringSession:
        q = select(TailoringSession).where(
            TailoringSession.id == session_id,
            TailoringSession.user_id == user_id,
        )
        session = await self._db.scalar(q)
        if session is None:
            raise NotFoundError(detail=f"Tailoring session {session_id} not found")
        return session

    async def _llm_json(self, prompt: str, *, stage: str) -> dict[str, Any]:
        try:
            result = await self._llm.chat_json(
                messages=[
                    {"role": "system", "content": "Return ONLY valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=2000,
            )
        except Exception as exc:
            logger.error(f"tailoring.{stage}_failed", error=str(exc))
            raise RuntimeError(f"Tailoring {stage} failed: {exc}") from exc
        logger.info(f"tailoring.{stage}_complete")
        return result

    @staticmethod
    def _ir_to_text(ir: dict[str, Any]) -> str:
        """Convert IR dict to plain text for parsed_text field."""
        parts: list[str] = []
        contact = ir.get("contact", {})
        if contact.get("name"):
            parts.append(contact["name"])

        if ir.get("summary"):
            parts.append(ir["summary"])

        for work in ir.get("work", []):
            company = work.get("company", "")
            title = work.get("title", "")
            parts.append(f"{company} - {title}")
            for bullet in work.get("bullets", []):
                parts.append(f"  - {bullet}")

        for edu in ir.get("education", []):
            inst = edu.get("institution", "")
            degree = edu.get("degree", "")
            parts.append(f"{inst} - {degree}")

        skills = ir.get("skills", [])
        if skills:
            parts.append("Skills: " + ", ".join(skills))

        return "\n".join(parts)
