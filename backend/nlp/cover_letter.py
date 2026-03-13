"""LLM-powered cover letter generation for job applications."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import FrozenSet, List

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

VALID_STYLES: FrozenSet[str] = frozenset({"professional", "conversational", "technical", "storytelling"})

_STYLE_INSTRUCTIONS: dict[str, str] = {
    "professional": (
        "Write in a formal, polished tone. Use clear business language. "
        "Structure: opening hook, 2 body paragraphs, confident closing."
    ),
    "conversational": (
        "Write in a warm, friendly tone as if speaking directly to the hiring manager. "
        "Avoid stiff language. Show genuine enthusiasm."
    ),
    "technical": (
        "Lead with technical achievements and concrete metrics. "
        "Use industry terminology. Demonstrate deep domain expertise."
    ),
    "storytelling": (
        "Open with a compelling personal story that connects to your passion for this role. "
        "Weave narrative throughout while connecting back to the job requirements."
    ),
}


@dataclass
class CoverLetter:
    """Result of LLM-powered cover letter generation."""

    content: str
    key_points_addressed: List[str]
    skills_highlighted: List[str]
    company_research_notes: List[str]
    word_count: int
    reading_level: str


_COVER_LETTER_PROMPT = """You are a professional cover letter writer. Generate a cover letter for the given job.

STYLE INSTRUCTIONS: {style_instructions}

RULES:
- Address the specific job requirements
- Highlight relevant skills and accomplishments from the resume
- Keep it under 400 words
- Never fabricate experience the candidate doesn't have
- Personalise to the company and role

Return ONLY valid JSON:
{{
  "content": "Full cover letter text...",
  "key_points_addressed": ["point1", "point2"],
  "skills_highlighted": ["skill1", "skill2"],
  "company_research_notes": ["note1"],
  "word_count": <integer>,
  "reading_level": "professional|conversational|technical"
}}

RESUME:
{resume_text}

JOB TITLE: {job_title}
COMPANY: {company_name}
JOB DESCRIPTION:
{job_description}

REQUIRED SKILLS: {required_skills}
"""


def _get_client(api_key: str) -> AsyncOpenAI:
    return AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


async def generate_cover_letter(
    resume_parsed: dict,
    job_data: dict,
    gap_analysis,       # GapAnalysis | None
    style: str,
    api_key: str,
) -> CoverLetter:
    """Generate a cover letter tailored to a specific job.

    Args:
        resume_parsed: Dict with keys 'text', 'skills', 'sections'.
        job_data:      Dict with keys 'title', 'description_clean',
                       'skills_required', 'company_name'.
        gap_analysis:  Optional GapAnalysis result.
        style:         One of VALID_STYLES.
        api_key:       OpenRouter API key.

    Returns:
        CoverLetter dataclass.

    Raises:
        ValueError: If style is invalid or resume has no text.
        RuntimeError: If the LLM call fails.
    """
    if style not in VALID_STYLES:
        raise ValueError(
            f"Invalid style {style!r}. Must be one of: {sorted(VALID_STYLES)}"
        )

    resume_text: str = (resume_parsed.get("text") or "").strip()
    if not resume_text:
        raise ValueError("Resume text is required for cover letter generation")

    client = _get_client(api_key)

    prompt = _COVER_LETTER_PROMPT.format(
        style_instructions=_STYLE_INSTRUCTIONS[style],
        resume_text=resume_text[:4000],
        job_title=job_data.get("title", ""),
        company_name=job_data.get("company_name", "the company"),
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
            temperature=0.3,
            max_tokens=1500,
        )
        data = json.loads(response.choices[0].message.content)
    except Exception as exc:
        logger.error("Cover letter generation failed: %s", exc)
        raise RuntimeError(f"LLM cover letter generation failed: {exc}") from exc

    return CoverLetter(
        content=data.get("content", ""),
        key_points_addressed=data.get("key_points_addressed", []),
        skills_highlighted=data.get("skills_highlighted", []),
        company_research_notes=data.get("company_research_notes", []),
        word_count=int(data.get("word_count", 0)),
        reading_level=data.get("reading_level", style),
    )
