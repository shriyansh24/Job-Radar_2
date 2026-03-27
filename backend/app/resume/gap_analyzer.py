"""Pure-Python gap analysis between a resume and a job posting.

No LLM calls — uses tokenization, cosine similarity, and transferable-skill
clustering.  Ported from v1's ``gap_analyzer.py``.
"""

from __future__ import annotations

import re
from typing import Any

from app.nlp.core import build_freq_map, cosine_similarity, tokenize

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TRANSFERABLE_CLUSTERS: list[frozenset[str]] = [
    frozenset(
        {
            "python",
            "java",
            "javascript",
            "typescript",
            "c#",
            "c++",
            "go",
            "ruby",
            "rust",
            "kotlin",
            "scala",
            "swift",
        }
    ),
    frozenset(
        {
            "fastapi",
            "flask",
            "django",
            "spring",
            "spring boot",
            "express",
            "rails",
            "laravel",
            "asp.net",
        }
    ),
    frozenset({"postgresql", "mysql", "sqlite", "mssql", "oracle", "mariadb"}),
    frozenset({"aws", "azure", "gcp", "google cloud"}),
    frozenset({"docker", "kubernetes", "helm", "podman"}),
    frozenset({"tensorflow", "pytorch", "keras", "scikit-learn", "xgboost"}),
    frozenset({"kafka", "rabbitmq", "sqs", "pubsub", "redis streams"}),
    frozenset({"terraform", "pulumi", "cloudformation", "ansible"}),
]

SENIORITY_WORDS: dict[str, float] = {
    "intern": 0.1,
    "junior": 0.2,
    "entry": 0.2,
    "associate": 0.3,
    "mid": 0.5,
    "intermediate": 0.5,
    "senior": 0.8,
    "staff": 0.85,
    "principal": 0.9,
    "lead": 0.85,
    "manager": 0.8,
    "director": 0.9,
    "vp": 0.95,
    "head": 0.9,
    "chief": 1.0,
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _normalize(text: str) -> str:
    return text.lower().strip()


def _skill_set(
    resume: dict[str, Any],
    job_data: dict[str, Any],
) -> tuple[frozenset[str], frozenset[str]]:
    """Return (resume_skills_lower, job_skills_lower)."""
    resume_skills: set[str] = {_normalize(s) for s in resume.get("skills", []) if s}
    job_skills: set[str] = set()
    for key in ("skills_required", "skills_nice_to_have", "tech_stack"):
        for s in job_data.get(key) or []:
            if s:
                job_skills.add(_normalize(s))
    return frozenset(resume_skills), frozenset(job_skills)


def _find_transferable(
    resume_skills: frozenset[str],
    missing: list[str],
) -> list[dict[str, str | float]]:
    results: list[dict[str, str | float]] = []
    for needed in missing:
        needed_lower = _normalize(needed)
        for cluster in TRANSFERABLE_CLUSTERS:
            if needed_lower not in cluster:
                continue
            for have in resume_skills:
                if have in cluster and have != needed_lower:
                    results.append({"have": have, "need": needed_lower, "relevance": 0.6})
                    break
    return results


def _keyword_density(resume_text: str, jd_text: str) -> float:
    jd_tokens = set(tokenize(jd_text))
    if not jd_tokens:
        return 0.0
    resume_tokens = set(tokenize(resume_text))
    return len(jd_tokens & resume_tokens) / len(jd_tokens)


def _experience_fit(resume_text: str, jd_text: str) -> float:
    def _dominant(text: str) -> float:
        text_lower = text.lower()
        scores = [
            score
            for word, score in SENIORITY_WORDS.items()
            if re.search(r"\b" + re.escape(word) + r"\b", text_lower)
        ]
        return sum(scores) / len(scores) if scores else 0.5

    return max(0.0, 1.0 - abs(_dominant(jd_text) - _dominant(resume_text)) * 2)


def _score_bullets(
    sections: dict[str, str],
    jd_text: str,
) -> tuple[list[str], list[str]]:
    if not sections or not jd_text.strip():
        return [], []

    jd_freq = build_freq_map(tokenize(jd_text))
    section_scores: list[tuple[str, float]] = []
    bullet_scores: list[tuple[str, float]] = []

    for name, text in sections.items():
        if not text:
            continue
        sec_freq = build_freq_map(tokenize(text))
        section_scores.append((name, cosine_similarity(sec_freq, jd_freq)))
        for sent in re.split(r"[.!?\n]", text):
            sent = sent.strip()
            if len(sent) < 20:
                continue
            sent_freq = build_freq_map(tokenize(sent))
            bullet_scores.append((sent, cosine_similarity(sent_freq, jd_freq)))

    bullet_scores.sort(key=lambda x: x[1], reverse=True)
    strongest = [b for b, _ in bullet_scores[:3]]

    section_scores.sort(key=lambda x: x[1])
    median_idx = max(1, len(section_scores) // 2)
    weakest = [name for name, _ in section_scores[:median_idx]]

    return strongest, weakest


def _ats_suggestions(missing_skills: list[str], jd_text: str, resume_text: str) -> list[str]:
    suggestions: list[str] = []
    if missing_skills:
        suggestions.append(
            f"Add missing keywords to your skills section: {', '.join(missing_skills[:5])}"
        )
    jd_tokens = tokenize(jd_text)
    resume_set = set(tokenize(resume_text))
    freq = build_freq_map(jd_tokens)
    high_freq_missing = [
        tok
        for tok, cnt in sorted(freq.items(), key=lambda x: -x[1])
        if cnt >= 2 and tok not in resume_set
    ][:5]
    if high_freq_missing:
        suggestions.append(
            "Consider weaving these high-frequency JD terms into your resume: "
            f"{', '.join(high_freq_missing)}"
        )
    if not suggestions:
        suggestions.append(
            "Your resume already contains the primary keywords from the job description."
        )
    return suggestions


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_gap_analysis(
    resume_parsed: dict[str, Any],
    job_data: dict[str, Any],
) -> dict[str, Any]:
    """Pure-Python gap analysis (no LLM).

    Parameters
    ----------
    resume_parsed:
        Dict with keys ``text`` (str), ``skills`` (list[str]),
        ``sections`` (dict[str, str]).
    job_data:
        Dict with keys ``title``, ``description_clean``,
        ``skills_required``, ``skills_nice_to_have``, ``tech_stack``.

    Returns a dict matching ``GapAnalysisResponse`` fields.
    """
    resume_text: str = resume_parsed.get("text", "") or ""
    sections: dict[str, str] = resume_parsed.get("sections", {}) or {}
    jd_text: str = (
        (job_data.get("description_clean", "") or "") + " " + (job_data.get("title", "") or "")
    )

    resume_skills, job_skills = _skill_set(resume_parsed, job_data)

    # Matched skills
    matched_raw = resume_skills & job_skills
    matched: list[dict[str, str | float]] = [
        {"skill": s, "confidence": 1.0} for s in sorted(matched_raw)
    ]

    # Substring matches in resume text (partial confidence)
    resume_lower = resume_text.lower()
    for skill in sorted(job_skills - matched_raw):
        if skill and skill in resume_lower:
            matched.append({"skill": skill, "confidence": 0.7})
            matched_raw = matched_raw | {skill}

    missing = sorted(job_skills - matched_raw)
    transferable = _find_transferable(resume_skills, missing)
    density = _keyword_density(resume_text, jd_text)
    exp_fit = _experience_fit(resume_text, jd_text)
    strongest, weakest = _score_bullets(sections, jd_text)
    suggestions = _ats_suggestions(missing, jd_text, resume_text)

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "transferable_skills": transferable,
        "keyword_density": round(density, 4),
        "experience_fit": round(exp_fit, 4),
        "ats_optimization_suggestions": suggestions,
        "strongest_bullets": strongest,
        "weakest_sections": weakest,
    }
