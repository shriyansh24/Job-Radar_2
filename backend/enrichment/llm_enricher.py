import json
import logging
from datetime import datetime

from openai import AsyncOpenAI
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database import async_session
from backend.models import Job

logger = logging.getLogger(__name__)

PRIMARY_MODEL = "anthropic/claude-3-5-haiku"
FALLBACK_MODEL = "openai/gpt-4o-mini"

ENRICHMENT_PROMPT = """
Analyze this job posting and return ONLY valid JSON with these exact keys:
{{
  "skills_required":     ["skill1", ...],
  "skills_nice_to_have": ["skill1", ...],
  "tech_stack":          ["Python", "AWS", ...],
  "experience_level":    "entry|mid|senior|exec",
  "job_type":            "full-time|part-time|contract|internship",
  "remote_type":         "remote|hybrid|onsite",
  "seniority_score":     0-100,
  "remote_score":        0-100,
  "summary_ai":          "2-3 sentence plain English summary",
  "red_flags":           ["max 3 strings"],
  "green_flags":         ["max 3 strings"]
}}

Job Title: {title}
Company: {company_name}
Description: {description}
"""


def _get_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "JobRadar",
        },
    )


async def enrich_job(job: Job, session: AsyncSession) -> bool:
    settings = get_settings()
    if not settings.OPENROUTER_API_KEY:
        logger.warning("OpenRouter API key not set, skipping enrichment")
        return False

    client = _get_client()
    description = (job.description_clean or "")[:3000]
    prompt = ENRICHMENT_PROMPT.format(
        title=job.title,
        company_name=job.company_name,
        description=description,
    )

    primary_model = settings.OPENROUTER_PRIMARY_MODEL or PRIMARY_MODEL
    fallback_model = settings.OPENROUTER_FALLBACK_MODEL or FALLBACK_MODEL

    for model in [primary_model, fallback_model]:
        try:
            response = await client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "Return ONLY valid JSON. No commentary."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=1000,
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            # Update job with enrichment data
            update_data = {
                "skills_required": data.get("skills_required"),
                "skills_nice_to_have": data.get("skills_nice_to_have"),
                "tech_stack": data.get("tech_stack"),
                "seniority_score": data.get("seniority_score"),
                "remote_score": data.get("remote_score"),
                "summary_ai": data.get("summary_ai"),
                "red_flags": data.get("red_flags"),
                "green_flags": data.get("green_flags"),
                "is_enriched": True,
                "enriched_at": datetime.utcnow(),
            }

            # Also update experience_level, job_type, remote_type if not already set
            if not job.experience_level and data.get("experience_level"):
                update_data["experience_level"] = data["experience_level"]
            if not job.job_type and data.get("job_type"):
                update_data["job_type"] = data["job_type"]
            if (not job.remote_type or job.remote_type == "unknown") and data.get("remote_type"):
                update_data["remote_type"] = data["remote_type"]

            await session.execute(
                update(Job).where(Job.job_id == job.job_id).values(**update_data)
            )
            await session.commit()

            logger.info(f"Enriched job: {job.title} @ {job.company_name} (model: {model})")
            return True

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error with {model}: {e}")
            continue
        except Exception as e:
            logger.warning(f"Enrichment failed with {model}: {e}")
            continue

    logger.error(f"Enrichment failed for job: {job.title} @ {job.company_name}")
    return False


async def run_enrichment_batch():
    async with async_session() as session:
        result = await session.execute(
            select(Job)
            .where(Job.is_enriched == False)
            .where(Job.description_clean.isnot(None))
            .where(Job.description_clean != "")
            .order_by(Job.scraped_at.desc())
            .limit(10)
        )
        jobs = result.scalars().all()

        if not jobs:
            logger.info("No unenriched jobs to process")
            return

        logger.info(f"Enrichment batch: processing {len(jobs)} jobs")
        enriched = 0
        for job in jobs:
            success = await enrich_job(job, session)
            if success:
                enriched += 1

        logger.info(f"Enrichment batch complete: {enriched}/{len(jobs)} enriched")
