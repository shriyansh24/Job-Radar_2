"""Answer evaluation logic for interview sessions.

Scores a candidate's answer via LLM and returns structured feedback.
Extracted from ``service.py`` so evaluation can be tested and evolved
independently of session management.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.interview.prompts import EVALUATE_ANSWER_PROMPT
from app.nlp.model_router import ModelRouter

logger = structlog.get_logger()


async def evaluate_answer(
    router: ModelRouter,
    *,
    job_title: str,
    company: str,
    question_text: str,
    answer_text: str,
) -> dict[str, Any]:
    """Call the LLM to score *answer_text* against the interview question.

    Parameters
    ----------
    router:
        A configured ``ModelRouter`` used for the LLM call.
    job_title:
        Title of the job being interviewed for.
    company:
        Name of the hiring company (falls back to ``"the company"``).
    question_text:
        The interview question the candidate was asked.
    answer_text:
        The candidate's raw answer to evaluate.

    Returns
    -------
    dict
        Keys: ``score`` (int), ``feedback`` (str),
        ``strengths`` (list[str]), ``improvements`` (list[str]).
    """
    prompt = EVALUATE_ANSWER_PROMPT.format(
        job_title=job_title,
        company=company or "the company",
        question=question_text,
        answer=answer_text,
    )

    messages: list[dict[str, str]] = [
        {"role": "system", "content": "Return ONLY valid JSON."},
        {"role": "user", "content": prompt},
    ]

    try:
        data = await router.complete_json(
            task="interview",
            messages=messages,
            temperature=0.3,
            max_tokens=800,
        )
    except RuntimeError:
        logger.exception("interview.evaluate_answer_failed")
        data = {
            "score": 0,
            "feedback": "Evaluation temporarily unavailable. Please try again.",
            "strengths": [],
            "improvements": [],
        }

    return {
        "score": data.get("score", 0),
        "feedback": data.get("feedback", ""),
        "strengths": data.get("strengths", []),
        "improvements": data.get("improvements", []),
    }
