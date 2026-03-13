"""Skill gap analysis between a parsed resume and a job description."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from backend.nlp.core import cosine_similarity, tokenize, build_freq_map

# ---------------------------------------------------------------------------
# Transferable skill clusters — skills in the same cluster are treated as
# partially transferable to each other.
# ---------------------------------------------------------------------------
_TRANSFERABLE_CLUSTERS: list[frozenset[str]] = [
    # General-purpose languages
    frozenset({"python", "java", "javascript", "typescript", "c#", "c++", "go", "ruby", "rust", "kotlin", "scala", "swift"}),
    # Web frameworks
    frozenset({"fastapi", "flask", "django", "spring", "spring boot", "express", "rails", "laravel", "asp.net"}),
    # Relational databases
    frozenset({"postgresql", "mysql", "sqlite", "mssql", "oracle", "mariadb"}),
    # Cloud platforms
    frozenset({"aws", "azure", "gcp", "google cloud"}),
    # Container / orchestration
    frozenset({"docker", "kubernetes", "helm", "podman"}),
    # ML frameworks
    frozenset({"tensorflow", "pytorch", "keras", "scikit-learn", "xgboost"}),
    # Message queues
    frozenset({"kafka", "rabbitmq", "sqs", "pubsub", "redis streams"}),
    # IaC tools
    frozenset({"terraform", "pulumi", "cloudformation", "ansible"}),
]

# Seniority signal words with associated numeric weight
_SENIORITY_WORDS: dict[str, float] = {
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


@dataclass
class GapAnalysis:
    """Result of comparing a parsed resume against a job posting."""

    # List of {skill: str, confidence: float 0-1}
    matched_skills: List[Dict] = field(default_factory=list)
    # Skills required by the job that are absent from the resume
    missing_skills: List[str] = field(default_factory=list)
    # {have: str, need: str, relevance: float} — cross-cluster partial matches
    transferable_skills: List[Dict] = field(default_factory=list)
    # Fraction of job-description keywords found in resume (0-1)
    keyword_density: float = 0.0
    # Estimated seniority alignment (0-1)
    experience_fit: float = 0.0
    # ATS keyword-stuffing suggestions
    ats_optimization_suggestions: List[str] = field(default_factory=list)
    # Top resume bullets most relevant to the JD
    strongest_bullets: List[str] = field(default_factory=list)
    # Resume sections with weak JD alignment
    weakest_sections: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    return text.lower().strip()


def _skill_set(resume: dict, job: dict) -> tuple[frozenset[str], frozenset[str]]:
    """Return (resume_skills_lower, job_skills_lower)."""
    # Collect resume skills from explicit list + free text
    resume_skills: set[str] = {_normalize(s) for s in resume.get("skills", []) if s}
    # Collect job skills from required + nice-to-have + tech_stack
    job_skills: set[str] = set()
    for lst_key in ("skills_required", "skills_nice_to_have", "tech_stack"):
        for s in job.get(lst_key, []) or []:
            if s:
                job_skills.add(_normalize(s))
    return frozenset(resume_skills), frozenset(job_skills)


def _find_transferable(
    resume_skills: frozenset[str],
    missing: list[str],
) -> list[dict]:
    """For each missing skill find a resume skill in the same cluster."""
    results: list[dict] = []
    for needed in missing:
        needed_lower = _normalize(needed)
        for cluster in _TRANSFERABLE_CLUSTERS:
            if needed_lower not in cluster:
                continue
            for have in resume_skills:
                if have in cluster and have != needed_lower:
                    results.append({"have": have, "need": needed_lower, "relevance": 0.6})
                    break
    return results


def _keyword_density(resume_text: str, jd_text: str) -> float:
    """Fraction of unique JD tokens (non-stopword) that appear in resume text."""
    jd_tokens = set(tokenize(jd_text))
    if not jd_tokens:
        return 0.0
    resume_tokens = set(tokenize(resume_text))
    overlap = jd_tokens & resume_tokens
    return len(overlap) / len(jd_tokens)


def _experience_fit(resume_text: str, jd_text: str) -> float:
    """Estimate seniority alignment: compare dominant level in JD vs resume."""
    def _dominant_level(text: str) -> float:
        text_lower = text.lower()
        scores = []
        for word, score in _SENIORITY_WORDS.items():
            if re.search(r"\b" + re.escape(word) + r"\b", text_lower):
                scores.append(score)
        return sum(scores) / len(scores) if scores else 0.5

    jd_level = _dominant_level(jd_text)
    resume_level = _dominant_level(resume_text)
    # Fit degrades with distance; cap at 1.0
    distance = abs(jd_level - resume_level)
    return max(0.0, 1.0 - distance * 2)


def _score_bullets(sections: dict, jd_text: str) -> tuple[list[str], list[str]]:
    """Return (strongest_bullets, weakest_section_names)."""
    if not sections or not jd_text.strip():
        return [], []

    jd_freq = build_freq_map(tokenize(jd_text))

    section_scores: list[tuple[str, float]] = []
    bullet_scores: list[tuple[str, float]] = []

    for section_name, section_text in sections.items():
        if not section_text:
            continue
        # Score whole section
        sec_freq = build_freq_map(tokenize(section_text))
        score = cosine_similarity(sec_freq, jd_freq)
        section_scores.append((section_name, score))

        # Score individual sentences as "bullets"
        sentences = re.split(r"[.!?\n]", section_text)
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 20:
                continue
            sent_freq = build_freq_map(tokenize(sent))
            s_score = cosine_similarity(sent_freq, jd_freq)
            bullet_scores.append((sent, s_score))

    # Sort bullets descending; take top 3
    bullet_scores.sort(key=lambda x: x[1], reverse=True)
    strongest = [b for b, _ in bullet_scores[:3]]

    # Weakest sections: bottom half by score
    section_scores.sort(key=lambda x: x[1])
    median_idx = max(1, len(section_scores) // 2)
    weakest = [name for name, _ in section_scores[:median_idx]]

    return strongest, weakest


def _ats_suggestions(missing_skills: list[str], jd_text: str, resume_text: str) -> list[str]:
    """Generate ATS keyword-stuffing suggestions."""
    suggestions: list[str] = []

    if missing_skills:
        skills_str = ", ".join(missing_skills[:5])
        suggestions.append(
            f"Add missing keywords to your skills section: {skills_str}"
        )

    # Find high-frequency JD phrases absent from resume
    jd_tokens = tokenize(jd_text)
    resume_tokens_set = set(tokenize(resume_text))
    freq = build_freq_map(jd_tokens)
    high_freq_missing = [
        tok for tok, count in sorted(freq.items(), key=lambda x: -x[1])
        if count >= 2 and tok not in resume_tokens_set
    ][:5]
    if high_freq_missing:
        suggestions.append(
            f"Consider weaving these high-frequency JD terms into your resume: {', '.join(high_freq_missing)}"
        )

    if not suggestions:
        suggestions.append("Your resume already contains the primary keywords from the job description.")

    return suggestions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_gaps(resume_parsed: dict, job_data: dict) -> GapAnalysis:
    """Analyse the skill gaps between a parsed resume and a job posting.

    Args:
        resume_parsed: Dict with keys 'text' (str), 'skills' (list[str]),
                       'sections' (dict[str, str]).
        job_data:      Dict with keys 'title', 'description_clean',
                       'skills_required', 'skills_nice_to_have', 'tech_stack'.

    Returns:
        GapAnalysis dataclass instance.
    """
    resume_text: str = resume_parsed.get("text", "") or ""
    sections: dict = resume_parsed.get("sections", {}) or {}
    jd_text: str = (job_data.get("description_clean", "") or "") + " " + (job_data.get("title", "") or "")

    resume_skills, job_skills = _skill_set(resume_parsed, job_data)

    # --- Matched skills ---
    matched_raw = resume_skills & job_skills
    matched: list[dict] = []
    for skill in sorted(matched_raw):
        # Confidence: exact name match → 1.0; case-fold match already done.
        matched.append({"skill": skill, "confidence": 1.0})

    # Also match skills via substring in resume text (partial confidence)
    resume_text_lower = resume_text.lower()
    for skill in sorted(job_skills - matched_raw):
        if skill and skill in resume_text_lower:
            matched.append({"skill": skill, "confidence": 0.7})
            matched_raw = matched_raw | {skill}

    # --- Missing skills ---
    missing = sorted(job_skills - matched_raw)

    # --- Transferable skills ---
    transferable = _find_transferable(resume_skills, missing)

    # --- Keyword density ---
    density = _keyword_density(resume_text, jd_text)

    # --- Experience fit ---
    exp_fit = _experience_fit(resume_text, jd_text)

    # --- Bullet scoring ---
    strongest, weakest = _score_bullets(sections, jd_text)

    # --- ATS suggestions ---
    ats_suggestions = _ats_suggestions(missing, jd_text, resume_text)

    return GapAnalysis(
        matched_skills=matched,
        missing_skills=missing,
        transferable_skills=transferable,
        keyword_density=density,
        experience_fit=exp_fit,
        ats_optimization_suggestions=ats_suggestions,
        strongest_bullets=strongest,
        weakest_sections=weakest,
    )
