"""TF-IDF job-resume matching scorer.

Algorithm (four components):
    raw = (base_cosine * 0.4) + (skill_bonus * 1.2) + (weight_adj * 0.5) + 40

    base_cosine  — cosine similarity of freq maps of job text vs resume text,
                   scaled to 0-100.
    skill_bonus  — matched_required_skills / total_required_skills * 100.
    weight_adj   — title similarity (0-100) + AI/ML domain keyword boost (0-30),
                   capped at 100 before weighting.

Final score is clamped to [10, 99].
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from backend.nlp.core import (
    build_freq_map,
    cosine_similarity,
    tokenize,
)

# ---------------------------------------------------------------------------
# Domain keyword boost configuration
# ---------------------------------------------------------------------------

_AI_ML_KEYWORDS: frozenset[str] = frozenset({
    "machine", "learning", "deep", "neural", "tensorflow", "pytorch", "keras",
    "scikit", "mlflow", "kubeflow", "mlops", "llm", "nlp", "bert", "gpt",
    "transformer", "embedding", "classification", "regression", "clustering",
    "reinforcement", "generative", "diffusion", "inference", "training",
    "gradient", "backpropagation", "convolutional", "recurrent", "lstm",
    "attention", "finetuning", "rlhf", "langchain", "openai", "huggingface",
    "xgboost", "lightgbm", "spark", "hadoop", "pipeline", "model", "dataset",
    "feature", "vector", "similarity", "retrieval", "rag",
})

# Weight applied per matching AI/ML keyword in both job and resume
_AI_ML_BOOST_PER_MATCH = 5
_AI_ML_BOOST_CAP = 30


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ScoringResult:
    """Result of a TF-IDF job-resume scoring operation.

    Attributes:
        score: Final clamped integer score in [10, 99].
        skill_matches: Required skills found in the resume.
        skill_gaps: Required skills NOT found in the resume.
        weight_breakdown: Dict with individual component values for transparency.
        explanation: Human-readable one-line summary.
    """

    score: int
    skill_matches: List[str] = field(default_factory=list)
    skill_gaps: List[str] = field(default_factory=list)
    weight_breakdown: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_skill(skill: str) -> str:
    """Lowercase and strip a skill string for comparison."""
    return skill.lower().strip()


def _skill_in_text(skill: str, token_set: frozenset[str]) -> bool:
    """Check whether a skill phrase appears in the token set.

    For multi-word skills (e.g. 'machine learning'), ALL component words must
    be present in the token set (each individually).  For single-word skills,
    an exact token match is required.
    """
    parts = re.findall(r"[a-z]+", skill.lower())
    # Drop single-char parts (punctuation artefacts)
    parts = [p for p in parts if len(p) > 1]
    if not parts:
        return False
    return all(p in token_set for p in parts)


def _compute_base_cosine(
    job_tokens: List[str], resume_tokens: List[str]
) -> float:
    """Cosine similarity between job description and resume freq maps, scaled 0-100."""
    job_freq = build_freq_map(job_tokens)
    resume_freq = build_freq_map(resume_tokens)
    return cosine_similarity(job_freq, resume_freq) * 100.0


def _compute_skill_bonus(
    required_skills: List[str],
    resume_token_set: frozenset[str],
) -> tuple[float, List[str], List[str]]:
    """Compute skill match ratio and return matched/gap lists.

    Returns:
        (bonus_0_100, skill_matches, skill_gaps)
    """
    if not required_skills:
        return 0.0, [], []

    matches: List[str] = []
    gaps: List[str] = []

    for skill in required_skills:
        if _skill_in_text(skill, resume_token_set):
            matches.append(skill)
        else:
            gaps.append(skill)

    bonus = (len(matches) / len(required_skills)) * 100.0
    return bonus, matches, gaps


def _compute_weight_adj(
    job_title: str,
    resume_text: str,
    job_tokens: List[str],
    resume_tokens: List[str],
) -> float:
    """Title similarity + AI/ML domain boost, combined and capped at 100.

    Components:
        title_sim  — cosine similarity of tokenised job title vs resume, scaled 0-100.
        ai_ml_boost — count of AI/ML keywords shared between job and resume, capped.
    """
    # Title similarity component
    title_tokens = tokenize(job_title)
    title_freq = build_freq_map(title_tokens)
    resume_freq = build_freq_map(resume_tokens)
    title_sim = cosine_similarity(title_freq, resume_freq) * 100.0

    # AI/ML domain keyword boost
    job_token_set = frozenset(job_tokens)
    resume_token_set = frozenset(resume_tokens)
    shared_ai_ml = _AI_ML_KEYWORDS & job_token_set & resume_token_set
    ai_ml_boost = min(len(shared_ai_ml) * _AI_ML_BOOST_PER_MATCH, _AI_ML_BOOST_CAP)

    return min(title_sim + ai_ml_boost, 100.0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_tfidf_score(
    job: Dict,
    resume: Dict,
) -> ScoringResult:
    """Compute a TF-IDF-based match score between a job posting and a resume.

    Args:
        job: Dict with keys:
            - title (str)
            - description_clean (str)
            - skills_required (list[str])
            - tech_stack (list[str])
        resume: Dict with keys:
            - text (str)  — full parsed resume text
            - skills (list[str])  — extracted resume skills

    Returns:
        ScoringResult with score clamped to [10, 99].

    Algorithm:
        raw = (base_cosine * 0.4) + (skill_bonus * 1.2) + (weight_adj * 0.5) + 40
        score = clamp(round(raw), 10, 99)
    """
    # ---- Extract inputs -------------------------------------------------------
    job_title: str = job.get("title") or ""
    job_desc: str = job.get("description_clean") or ""
    job_skills_required: List[str] = list(job.get("skills_required") or [])
    job_tech_stack: List[str] = list(job.get("tech_stack") or [])

    resume_text: str = resume.get("text") or ""
    resume_skills: List[str] = list(resume.get("skills") or [])

    # Merge tech_stack into required skills for matching purposes (deduped)
    all_required = list({_normalize_skill(s) for s in job_skills_required + job_tech_stack})

    # Build full job text: title + description
    full_job_text = f"{job_title} {job_desc}"

    # Build full resume text: provided text + listed skills joined
    full_resume_text = f"{resume_text} {' '.join(resume_skills)}"

    # Tokenize
    job_tokens = tokenize(full_job_text)
    resume_tokens = tokenize(full_resume_text)
    resume_token_set = frozenset(resume_tokens)

    # ---- Component 1: base cosine ---------------------------------------------
    base_cosine = _compute_base_cosine(job_tokens, resume_tokens)

    # ---- Component 2: skill bonus ---------------------------------------------
    # Use normalised combined required+tech_stack for matching
    skill_bonus, skill_matches, skill_gaps = _compute_skill_bonus(
        all_required, resume_token_set
    )

    # ---- Component 3: weight_adj (title sim + domain boost) ------------------
    weight_adj = _compute_weight_adj(job_title, resume_text, job_tokens, resume_tokens)

    # ---- Final formula --------------------------------------------------------
    raw = (base_cosine * 0.4) + (skill_bonus * 1.2) + (weight_adj * 0.5) + 40
    score = max(10, min(99, round(raw)))

    # ---- Build explanation ---------------------------------------------------
    n_match = len(skill_matches)
    n_total = len(all_required)
    if n_total > 0:
        explanation = (
            f"Score {score}/99 — matched {n_match}/{n_total} required skills; "
            f"text similarity {base_cosine:.0f}/100."
        )
    else:
        explanation = (
            f"Score {score}/99 — no required skills listed; "
            f"text similarity {base_cosine:.0f}/100."
        )

    weight_breakdown = {
        "base_cosine": round(base_cosine, 2),
        "skill_bonus": round(skill_bonus, 2),
        "weight_adj": round(weight_adj, 2),
        "raw_before_clamp": round(raw, 2),
    }

    return ScoringResult(
        score=score,
        skill_matches=skill_matches,
        skill_gaps=skill_gaps,
        weight_breakdown=weight_breakdown,
        explanation=explanation,
    )
