from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog

from app.config import Settings
from app.enrichment.llm_client import LLMClient

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.jobs.models import Job

logger = structlog.get_logger()


class EnrichmentError(RuntimeError):
    """Raised when the LLM enrichment response is missing or unusable."""


class EnrichmentService:
    """AI-powered job enrichment: summary, skills, scoring."""

    def __init__(self, db: AsyncSession, llm_client: LLMClient, settings: Settings):
        self.db = db
        self.llm = llm_client
        self.settings = settings

    async def enrich_job(self, job: "Job") -> "Job":
        """Full enrichment pipeline for a single job.

        Accepts a Job ORM object and mutates it in place.
        """
        desc_raw = getattr(job, "description_raw", None)
        if not desc_raw:
            return job

        tracked_fields = (
            "description_clean",
            "description_markdown",
            "summary_ai",
            "skills_required",
            "skills_nice_to_have",
            "tech_stack",
            "red_flags",
            "green_flags",
            "salary_min",
            "salary_max",
            "salary_period",
            "experience_level",
            "seniority_score",
            "is_enriched",
            "enriched_at",
        )
        snapshot = {field: getattr(job, field, None) for field in tracked_fields}

        try:
            clean_description = self._clean_html(desc_raw)
            markdown_description = self._html_to_markdown(desc_raw)

            # 1. LLM enrichment (summary + skills + flags)
            enrichment = await self._llm_enrich(job, clean_description)

            # 2. Persist cleaned description and enrichment payload only after success.
            job.description_clean = clean_description  # type: ignore[attr-defined]
            job.description_markdown = markdown_description  # type: ignore[attr-defined]
            job.summary_ai = enrichment.get("summary")  # type: ignore[attr-defined]
            job.skills_required = enrichment.get("skills_required", [])  # type: ignore[attr-defined]
            job.skills_nice_to_have = enrichment.get("skills_nice_to_have", [])  # type: ignore[attr-defined]
            job.tech_stack = enrichment.get("tech_stack", [])  # type: ignore[attr-defined]
            job.red_flags = enrichment.get("red_flags", [])  # type: ignore[attr-defined]
            job.green_flags = enrichment.get("green_flags", [])  # type: ignore[attr-defined]

            # 3. Extract salary if not present
            if not getattr(job, "salary_min", None) and not getattr(job, "salary_max", None):
                sal = enrichment.get("salary_estimate")
                if sal and isinstance(sal, dict):
                    job.salary_min = sal.get("min")  # type: ignore[attr-defined]
                    job.salary_max = sal.get("max")  # type: ignore[attr-defined]
                    job.salary_period = sal.get("period", "annual")  # type: ignore[attr-defined]

            # 4. Determine experience level if missing
            if not getattr(job, "experience_level", None):
                job.experience_level = enrichment.get("experience_level")  # type: ignore[attr-defined]
                job.seniority_score = enrichment.get("seniority_score")  # type: ignore[attr-defined]

            job.is_enriched = True  # type: ignore[attr-defined]
            job.enriched_at = datetime.now(UTC)  # type: ignore[attr-defined]
            return job
        except Exception:
            for field, value in snapshot.items():
                setattr(job, field, value)
            raise

    async def _llm_enrich(self, job: object, description_clean: str) -> dict:
        """Call LLM to extract structured info from job description."""
        title = getattr(job, "title", "")
        company = getattr(job, "company_name", "")
        location = getattr(job, "location", "")
        desc = description_clean

        prompt = f"""Analyze this job posting and extract structured information.

Job Title: {title}
Company: {company}
Location: {location}

Description:
{desc[:4000]}

Return a JSON object with these fields:
- summary: 2-3 sentence summary of the role
- skills_required: list of required skills/technologies
- skills_nice_to_have: list of nice-to-have skills
- tech_stack: list of specific technologies mentioned
- red_flags: list of concerning aspects (unrealistic requirements, etc.)
- green_flags: list of positive aspects (good benefits, growth, etc.)
- experience_level: one of entry/mid/senior/lead/executive
- seniority_score: 1-10 scale
- salary_estimate: {{"min": number, "max": number, "period": "annual"}} or null

Return ONLY valid JSON, no markdown."""

        response = await self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500,
        )

        if not response:
            raise EnrichmentError("LLM enrichment returned an empty response")

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            logger.warning("llm_json_parse_failed", response_preview=response[:200])
            raise EnrichmentError("LLM enrichment returned invalid JSON")

    async def enrich_batch(self, user_id: uuid.UUID | None = None, limit: int = 50) -> int:
        """Enrich unenriched jobs in batch."""
        try:
            from sqlalchemy import select

            from app.jobs.models import Job
        except ImportError:
            logger.warning("job_model_not_available")
            return 0

        query = (
            select(Job)
            .where(
                Job.is_enriched == False,  # noqa: E712
                Job.description_raw.isnot(None),
            )
            .limit(limit)
        )
        if user_id:
            query = query.where(Job.user_id == user_id)

        jobs = (await self.db.scalars(query)).all()

        count = 0
        for job in jobs:
            try:
                await self.enrich_job(job)
                count += 1
            except Exception as e:
                logger.error("enrichment_failed", job_id=job.id, error=str(e))
        await self.db.commit()
        logger.info("enrichment_batch_done", enriched=count, total=len(jobs))
        return count

    def _clean_html(self, html: str) -> str:
        """Strip HTML tags, normalize whitespace."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator="\n", strip=True)

    def _html_to_markdown(self, html: str) -> str:
        """Convert HTML to Markdown."""
        try:
            import markdownify

            return markdownify.markdownify(html, heading_style="ATX")
        except ImportError:
            return self._clean_html(html)
