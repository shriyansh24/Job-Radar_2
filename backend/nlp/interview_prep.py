"""LLM-powered interview preparation for job applications."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import List

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


@dataclass
class InterviewPrep:
    """Result of LLM-powered interview preparation."""

    # {question: str, category: "behavioral"|"technical"|"situational"}
    likely_questions: List[dict]
    # {situation: str, task: str, action: str, result: str}
    star_stories: List[dict]
    # Technical topic areas to study
    technical_topics: List[str]
    # Talking points about the company / role
    company_talking_points: List[str]
    # Questions the candidate should ask the interviewer
    questions_to_ask: List[str]
    # {question: str, avoid: str, instead: str}
    red_flag_responses: List[dict]


_INTERVIEW_PREP_PROMPT = """You are an expert interview coach. Prepare this candidate for their interview.

Return ONLY valid JSON:
{{
  "likely_questions": [
    {{"question": "...", "category": "behavioral|technical|situational"}}
  ],
  "star_stories": [
    {{"situation": "...", "task": "...", "action": "...", "result": "..."}}
  ],
  "technical_topics": ["topic1", "topic2"],
  "company_talking_points": ["point1", "point2"],
  "questions_to_ask": ["question1", "question2"],
  "red_flag_responses": [
    {{"question": "...", "avoid": "...", "instead": "..."}}
  ]
}}

RULES:
- Generate 5-8 likely questions mixing behavioral and technical
- Create 2-3 STAR stories from the resume experience
- List 3-5 technical topics to brush up on based on job requirements
- Suggest 3-5 smart questions to ask the interviewer
- Flag 2-3 common interview pitfalls with better alternatives

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


async def generate_interview_prep(
    resume_parsed: dict,
    job_data: dict,
    gap_analysis,       # GapAnalysis | None
    api_key: str,
) -> InterviewPrep:
    """Generate interview preparation material for a specific job.

    Args:
        resume_parsed: Dict with keys 'text', 'skills', 'sections'.
        job_data:      Dict with keys 'title', 'description_clean',
                       'skills_required', 'company_name'.
        gap_analysis:  Optional GapAnalysis result.
        api_key:       OpenRouter API key.

    Returns:
        InterviewPrep dataclass.

    Raises:
        ValueError: If resume has no text.
        RuntimeError: If the LLM call fails.
    """
    resume_text: str = (resume_parsed.get("text") or "").strip()
    if not resume_text:
        raise ValueError("Resume text is required for interview preparation")

    client = _get_client(api_key)

    prompt = _INTERVIEW_PREP_PROMPT.format(
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
                {"role": "system", "content": "Return ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2000,
        )
        data = json.loads(response.choices[0].message.content)
    except Exception as exc:
        logger.error("Interview prep generation failed: %s", exc)
        raise RuntimeError(f"LLM interview prep generation failed: {exc}") from exc

    return InterviewPrep(
        likely_questions=data.get("likely_questions", []),
        star_stories=data.get("star_stories", []),
        technical_topics=data.get("technical_topics", []),
        company_talking_points=data.get("company_talking_points", []),
        questions_to_ask=data.get("questions_to_ask", []),
        red_flag_responses=data.get("red_flag_responses", []),
    )
