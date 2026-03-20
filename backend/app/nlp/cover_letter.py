"""LLM-powered cover letter generation for job applications.

Ported from v1 -- uses v2's LLMClient and ModelRouter for API calls
with automatic model fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, FrozenSet, List, Optional

import structlog

from app.config import settings
from app.enrichment.llm_client import LLMClient
from app.nlp.cover_letter_templates import (
    VALID_TEMPLATES,
    build_template_prompt_section,
    get_template,
)
from app.nlp.model_router import ModelRouter

logger = structlog.get_logger()

VALID_STYLES: FrozenSet[str] = frozenset(
    {"professional", "conversational", "technical", "storytelling"}
)

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
class CoverLetterResult:
    """Result of LLM-powered cover letter generation."""

    content: str
    key_points_addressed: List[str]
    skills_highlighted: List[str]
    company_research_notes: List[str]
    word_count: int
    reading_level: str


_COVER_LETTER_PROMPT = """You are a professional cover letter writer. Generate a cover letter for the given job.

STYLE INSTRUCTIONS: {style_instructions}

{template_section}RULES:
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


def _get_llm_client() -> LLMClient:
    """Build an LLMClient from app settings."""
    return LLMClient(
        api_key=settings.openrouter_api_key,
        model=settings.default_llm_model,
    )


def _get_model_router() -> ModelRouter:
    """Build a ModelRouter wrapping the shared LLMClient."""
    return ModelRouter(_get_llm_client())


async def generate_cover_letter(
    resume_parsed: dict[str, Any],
    job_data: dict[str, Any],
    style: str,
    template: Optional[str] = None,
) -> CoverLetterResult:
    """Generate a cover letter tailored to a specific job.

    Args:
        resume_parsed: Dict with keys 'text', 'skills', 'sections'.
        job_data:      Dict with keys 'title', 'description_clean',
                       'skills_required', 'company_name'.
        style:         One of VALID_STYLES.
        template:      Optional template name -- one of VALID_TEMPLATES
                       ('formal', 'startup', 'career-change', 'technical').
                       Defaults to 'formal' when None.

    Returns:
        CoverLetterResult dataclass.

    Raises:
        ValueError: If style or template is invalid, or resume has no text.
        RuntimeError: If the LLM call fails.
    """
    if style not in VALID_STYLES:
        raise ValueError(
            f"Invalid style {style!r}. Must be one of: {sorted(VALID_STYLES)}"
        )

    # Resolve template -- default to "formal" when not specified.
    resolved_template_name: str = template if template is not None else "formal"
    if resolved_template_name not in VALID_TEMPLATES:
        raise ValueError(
            f"Invalid template {resolved_template_name!r}. "
            f"Must be one of: {sorted(VALID_TEMPLATES)}"
        )
    cover_letter_template = get_template(resolved_template_name)
    template_section = build_template_prompt_section(cover_letter_template) + "\n\n"

    resume_text: str = (resume_parsed.get("text") or "").strip()
    if not resume_text:
        raise ValueError("Resume text is required for cover letter generation")

    prompt = _COVER_LETTER_PROMPT.format(
        style_instructions=_STYLE_INSTRUCTIONS[style],
        template_section=template_section,
        resume_text=resume_text[:4000],
        job_title=job_data.get("title", ""),
        company_name=job_data.get("company_name", "the company"),
        job_description=(job_data.get("description_clean", "") or "")[:3000],
        required_skills=", ".join(job_data.get("skills_required", []) or []),
    )

    messages = [
        {
            "role": "system",
            "content": "Return ONLY valid JSON. Never fabricate experience.",
        },
        {"role": "user", "content": prompt},
    ]

    router = _get_model_router()
    llm = router._llm  # keep reference to close later

    try:
        logger.info(
            "cover_letter_generating",
            style=style,
            template=resolved_template_name,
            job_title=job_data.get("title", ""),
        )

        data = await router.complete_json(
            task="cover_letter",
            messages=messages,
            temperature=0.3,
            max_tokens=1500,
        )
    except Exception as exc:
        logger.error("cover_letter_generation_failed", error=str(exc))
        raise RuntimeError(f"LLM cover letter generation failed: {exc}") from exc
    finally:
        await llm.close()

    if not data:
        raise RuntimeError("Cover letter generation returned empty response")

    result = CoverLetterResult(
        content=data.get("content", ""),
        key_points_addressed=data.get("key_points_addressed", []),
        skills_highlighted=data.get("skills_highlighted", []),
        company_research_notes=data.get("company_research_notes", []),
        word_count=int(data.get("word_count", 0)),
        reading_level=data.get("reading_level", style),
    )

    logger.info(
        "cover_letter_generated",
        style=style,
        template=resolved_template_name,
        word_count=result.word_count,
    )
    return result
