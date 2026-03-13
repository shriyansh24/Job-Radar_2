"""3-model council scoring system for resume-job matching."""
import json
import asyncio
from dataclasses import dataclass, field
from openai import AsyncOpenAI


SCORING_DIMENSIONS = [
    "skill_alignment",
    "experience_level",
    "impact_language",
    "ats_keyword_density",
    "structural_quality",
    "cultural_signals",
    "growth_trajectory",
]

COUNCIL_MODELS = [
    "anthropic/claude-3-5-haiku",
    "openai/gpt-4o-mini",
    "google/gemini-flash-1.5",
]

COUNCIL_PROMPT = """You are evaluating a resume against a job description. Score each dimension 0-100 with a letter grade.

Return ONLY valid JSON with this exact structure:
{{
  "skill_alignment": {{"grade": "A/B/C/D", "score": 0-100, "rationale": "...", "gaps": [...], "suggestions": [...]}},
  "experience_level": {{"grade": "...", "score": 0-100, "rationale": "...", "gaps": [...], "suggestions": [...]}},
  "impact_language": {{"grade": "...", "score": 0-100, "rationale": "...", "gaps": [...], "suggestions": [...]}},
  "ats_keyword_density": {{"grade": "...", "score": 0-100, "rationale": "...", "gaps": [...], "suggestions": [...]}},
  "structural_quality": {{"grade": "...", "score": 0-100, "rationale": "...", "gaps": [...], "suggestions": [...]}},
  "cultural_signals": {{"grade": "...", "score": 0-100, "rationale": "...", "gaps": [...], "suggestions": [...]}},
  "growth_trajectory": {{"grade": "...", "score": 0-100, "rationale": "...", "gaps": [...], "suggestions": [...]}},
  "overall_grade": "A/B/C/D",
  "overall_score": 0-100,
  "top_gaps": ["..."],
  "missing_keywords": ["..."],
  "strong_points": ["..."],
  "suggested_bullets": ["..."]
}}

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}
"""


@dataclass
class DimensionScore:
    grade: str
    score: int
    rationale: str
    gaps: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class CouncilScore:
    skill_alignment: DimensionScore
    experience_level: DimensionScore
    impact_language: DimensionScore
    ats_keyword_density: DimensionScore
    structural_quality: DimensionScore
    cultural_signals: DimensionScore
    growth_trajectory: DimensionScore
    overall_grade: str
    overall_score: int
    top_gaps: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    strong_points: list[str] = field(default_factory=list)
    suggested_bullets: list[str] = field(default_factory=list)
    council_consensus: float = 0.0


def _get_openrouter_client(api_key: str) -> AsyncOpenAI:
    return AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


def _parse_model_response(content: str) -> dict | None:
    """Parse a model's JSON response. Returns None on failure."""
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
        return None
    except (json.JSONDecodeError, TypeError):
        return None


def _aggregate_scores(responses: list[dict]) -> CouncilScore:
    """Average multiple model responses into a single CouncilScore."""
    if not responses:
        raise ValueError("No valid model responses to aggregate")

    n = len(responses)

    # Average each dimension's score
    aggregated: dict[str, DimensionScore] = {}
    for dim in SCORING_DIMENSIONS:
        scores = []
        all_gaps: list[str] = []
        all_suggestions: list[str] = []
        grades: list[str] = []
        rationales: list[str] = []

        for resp in responses:
            if dim in resp and isinstance(resp[dim], dict):
                d = resp[dim]
                scores.append(d.get("score", 0))
                grades.append(d.get("grade", "C"))
                rationales.append(d.get("rationale", ""))
                all_gaps.extend(d.get("gaps", []))
                all_suggestions.extend(d.get("suggestions", []))

        avg_score = round(sum(scores) / len(scores)) if scores else 0
        # Most common grade
        grade = max(set(grades), key=grades.count) if grades else "C"
        rationale = rationales[0] if rationales else ""

        aggregated[dim] = DimensionScore(
            grade=grade,
            score=avg_score,
            rationale=rationale,
            gaps=list(set(all_gaps)),
            suggestions=list(set(all_suggestions)),
        )

    # Average overall score
    overall_scores = [r.get("overall_score", 0) for r in responses if "overall_score" in r]
    avg_overall = round(sum(overall_scores) / len(overall_scores)) if overall_scores else 0

    # Overall grade from majority
    overall_grades = [r.get("overall_grade", "C") for r in responses if "overall_grade" in r]
    overall_grade = max(set(overall_grades), key=overall_grades.count) if overall_grades else "C"

    # Consensus: 1.0 - normalized std deviation of overall scores
    if len(overall_scores) > 1:
        mean = sum(overall_scores) / len(overall_scores)
        variance = sum((s - mean) ** 2 for s in overall_scores) / len(overall_scores)
        std_dev = variance ** 0.5
        consensus = max(0.0, 1.0 - (std_dev / 50.0))  # 50-point spread = 0 consensus
    else:
        consensus = 1.0

    # Merge lists (deduplicated)
    all_gap_list = list(set(g for r in responses for g in r.get("top_gaps", [])))
    all_keywords = list(set(k for r in responses for k in r.get("missing_keywords", [])))
    all_strong = list(set(s for r in responses for s in r.get("strong_points", [])))
    all_bullets = list(set(b for r in responses for b in r.get("suggested_bullets", [])))

    return CouncilScore(
        **aggregated,
        overall_grade=overall_grade,
        overall_score=avg_overall,
        top_gaps=all_gap_list,
        missing_keywords=all_keywords,
        strong_points=all_strong,
        suggested_bullets=all_bullets,
        council_consensus=round(consensus, 3),
    )


async def evaluate_resume_council(
    resume_text: str,
    job_description: str,
    api_key: str,
) -> CouncilScore:
    """Run all 3 council models in parallel and aggregate their scores."""
    if not resume_text.strip() or not job_description.strip():
        raise ValueError("Resume text and job description are required")

    client = _get_openrouter_client(api_key)
    prompt = COUNCIL_PROMPT.format(
        resume_text=resume_text[:5000],
        job_description=job_description[:3000],
    )

    async def _call_model(model: str) -> dict | None:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Return ONLY valid JSON. No commentary."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2000,
            )
            return _parse_model_response(response.choices[0].message.content)
        except Exception:
            return None

    # Run all 3 models in parallel
    results = await asyncio.gather(*[_call_model(m) for m in COUNCIL_MODELS])
    valid_results = [r for r in results if r is not None]

    if not valid_results:
        raise RuntimeError("All council models failed to respond")

    return _aggregate_scores(valid_results)
