"""LLM-powered resume tailoring for job applications."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import List

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


@dataclass
class TailoredResume:
    """Result of LLM-powered resume tailoring."""

    summary: str
    reordered_experience: List[dict]
    enhanced_bullets: List[dict]   # {original: str, enhanced: str}
    skills_section: List[str]
    ats_score_before: int
    ats_score_after: int


TAILOR_PROMPT = """You are a professional resume writer. Tailor this resume for the given job.

RULES:
- Never fabricate experience or skills the candidate doesn't have
- Enhance existing bullets with stronger action verbs and quantified results
- Reorder experience to highlight most relevant roles first
- Add missing keywords from the job description where the candidate has relevant experience
- Generate a targeted professional summary

Return ONLY valid JSON:
{{
  "summary": "2-3 sentence professional summary tailored to this role",
  "reordered_experience": [{{"company": "...", "bullets": ["..."]}}],
  "enhanced_bullets": [{{"original": "...", "enhanced": "..."}}],
  "skills_section": ["skill1", "skill2"],
  "ats_score_before": 0-100,
  "ats_score_after": 0-100
}}

RESUME:
{resume_text}

JOB TITLE: {job_title}
JOB DESCRIPTION:
{job_description}

REQUIRED SKILLS: {required_skills}
"""


def _get_client(api_key: str) -> AsyncOpenAI:
    return AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


async def tailor_resume(
    resume_parsed: dict,
    job_data: dict,
    gap_analysis,       # GapAnalysis | None
    api_key: str,
) -> TailoredResume:
    """Tailor a resume for a specific job using an LLM.

    Args:
        resume_parsed: Dict with keys 'text', 'skills', 'sections'.
        job_data:      Dict with keys 'title', 'description_clean', 'skills_required'.
        gap_analysis:  Optional GapAnalysis result (used to enrich the prompt).
        api_key:       OpenRouter API key.

    Returns:
        TailoredResume dataclass.

    Raises:
        ValueError: If resume_parsed contains no text.
        RuntimeError: If the LLM call fails.
    """
    resume_text: str = (resume_parsed.get("text") or "").strip()
    if not resume_text:
        raise ValueError("Resume text is required for tailoring")

    client = _get_client(api_key)

    prompt = TAILOR_PROMPT.format(
        resume_text=resume_text[:4000],
        job_title=job_data.get("title", ""),
        job_description=(job_data.get("description_clean", "") or "")[:3000],
        required_skills=", ".join(job_data.get("skills_required", []) or []),
    )

    try:
        response = await client.chat.completions.create(
            model="anthropic/claude-3-5-haiku",
            messages=[
                {"role": "system", "content": "Return ONLY valid JSON. Never fabricate experience."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=2000,
        )
        data = json.loads(response.choices[0].message.content)
    except Exception as exc:
        logger.error("Resume tailoring failed: %s", exc)
        raise RuntimeError(f"LLM tailoring failed: {exc}") from exc

    return TailoredResume(
        summary=data.get("summary", ""),
        reordered_experience=data.get("reordered_experience", []),
        enhanced_bullets=data.get("enhanced_bullets", []),
        skills_section=data.get("skills_section", []),
        ats_score_before=int(data.get("ats_score_before", 0)),
        ats_score_after=int(data.get("ats_score_after", 0)),
    )
