"""Multi-model council evaluation for resumes.

Sends the same evaluation prompt to several LLM models concurrently
and aggregates their scores into an overall consensus.
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from app.enrichment.llm_client import LLMClient
from app.resume.prompts import COUNCIL_PROMPT

logger = structlog.get_logger()

# Models used for the multi-model council
COUNCIL_MODELS: list[str] = [
    "anthropic/claude-3-5-sonnet-20241022",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
]


async def council_evaluate(
    *,
    resume_text: str,
    job_title: str,
    job_description: str,
    llm_client: LLMClient,
) -> dict[str, Any]:
    """Evaluate a resume with multiple LLM models and aggregate scores.

    Parameters
    ----------
    resume_text:
        Plain-text resume content.
    job_title:
        Target job title (falls back to a generic description).
    job_description:
        Cleaned job-description text (falls back to a generic prompt).
    llm_client:
        An ``LLMClient`` instance used to call each council model.

    Returns a dict matching ``CouncilResponse`` fields.
    """
    prompt = COUNCIL_PROMPT.format(
        resume_text=resume_text[:4000],
        job_title=job_title or "General software engineering position",
        job_description=job_description or "Evaluate the resume for general quality and impact.",
    )

    messages = [
        {"role": "system", "content": "Return ONLY valid JSON. Be critical and constructive."},
        {"role": "user", "content": prompt},
    ]

    # ------------------------------------------------------------------
    # Run evaluations concurrently across council models
    # ------------------------------------------------------------------

    async def _evaluate(model: str) -> dict[str, Any] | None:
        try:
            result = await llm_client.chat_json(
                messages=messages,
                temperature=0.3,
                max_tokens=1500,
                model=model,
            )
            if result:
                result["_model"] = model
                return result
            return None
        except Exception as exc:
            logger.warning(
                "resume.council.model_failed",
                model=model,
                error=str(exc),
            )
            return None

    results = await asyncio.gather(
        *[_evaluate(m) for m in COUNCIL_MODELS],
        return_exceptions=False,
    )

    # ------------------------------------------------------------------
    # Aggregate scores
    # ------------------------------------------------------------------

    evaluations: list[dict[str, Any]] = []
    scores: list[float] = []
    for res in results:
        if res is None:
            continue
        model_name = res.pop("_model", "unknown")
        score = float(res.get("score", 0))
        evaluations.append(
            {
                "model": model_name,
                "score": score,
                "feedback": res.get("feedback", ""),
                "strengths": res.get("strengths", []),
                "weaknesses": res.get("weaknesses", []),
            }
        )
        scores.append(score)

    overall = round(sum(scores) / len(scores), 1) if scores else None

    # Build consensus summary
    if len(scores) >= 2:
        avg = overall
        spread = max(scores) - min(scores)
        if spread <= 10:
            consensus = f"Strong consensus: models agree on a score of ~{avg}"
        elif spread <= 25:
            consensus = (
                f"Moderate consensus: scores range from {min(scores):.0f} to "
                f"{max(scores):.0f} (avg {avg})"
            )
        else:
            consensus = (
                f"Divergent opinions: scores range widely from {min(scores):.0f} to "
                f"{max(scores):.0f}"
            )
    elif len(scores) == 1:
        consensus = "Single model evaluation (other models failed)"
    else:
        consensus = "All council models failed to provide evaluations"

    return {
        "evaluations": evaluations,
        "overall_score": overall,
        "consensus": consensus,
    }
