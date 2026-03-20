from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResumeVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str | None = None
    filename: str | None = None
    parsed_text: str | None = None
    parsed_structured: dict | None = None
    is_default: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Resume Tailoring
# ---------------------------------------------------------------------------


class ResumeTailorRequest(BaseModel):
    job_id: str
    resume_version_id: uuid.UUID | None = None


class EnhancedBullet(BaseModel):
    original: str
    enhanced: str


class PartialMatch(BaseModel):
    requirement: str
    evidence: str
    gap: str


class KeywordCoverage(BaseModel):
    present: list[str] = []
    missing: list[str] = []


class Stage1Output(BaseModel):
    """Stage 1: Job description analysis output."""
    hard_requirements: list[str] = []
    soft_requirements: list[str] = []
    key_technologies: list[str] = []
    ats_keywords: list[str] = []
    culture_signals: list[str] = []
    seniority_indicators: list[str] = []
    deal_breakers: list[str] = []


class Stage2Output(BaseModel):
    """Stage 2: Gap mapping output."""
    matched_requirements: list[str] = []
    partial_matches: list[PartialMatch] = []
    missing_requirements: list[str] = []
    transferable_skills: list[str] = []
    keyword_coverage: KeywordCoverage = Field(default_factory=KeywordCoverage)
    strength_areas: list[str] = []
    risk_areas: list[str] = []


class ReorderedExperience(BaseModel):
    company: str
    bullets: list[str] = []


class ResumeTailorResponse(BaseModel):
    summary: str = ""
    reordered_experience: list[ReorderedExperience] = []
    enhanced_bullets: list[EnhancedBullet] = []
    skills_section: list[str] = []
    ats_score_before: int = 0
    ats_score_after: int = 0
    stage1_output: Stage1Output | None = None
    stage2_output: Stage2Output | None = None


# ---------------------------------------------------------------------------
# Gap Analysis
# ---------------------------------------------------------------------------


class GapAnalysisRequest(BaseModel):
    resume_version_id: uuid.UUID
    job_id: str


class MatchedSkill(BaseModel):
    skill: str
    confidence: float


class TransferableSkill(BaseModel):
    have: str
    need: str
    relevance: float


class GapAnalysisResponse(BaseModel):
    matched_skills: list[MatchedSkill] = []
    missing_skills: list[str] = []
    transferable_skills: list[TransferableSkill] = []
    keyword_density: float = 0.0
    experience_fit: float = 0.0
    ats_optimization_suggestions: list[str] = []
    strongest_bullets: list[str] = []
    weakest_sections: list[str] = []


# ---------------------------------------------------------------------------
# Council Evaluation
# ---------------------------------------------------------------------------


class CouncilRequest(BaseModel):
    resume_version_id: uuid.UUID
    job_id: str | None = None


class CouncilEvaluation(BaseModel):
    model: str
    score: float
    feedback: str
    strengths: list[str] = []
    weaknesses: list[str] = []


class CouncilResponse(BaseModel):
    evaluations: list[CouncilEvaluation] = []
    overall_score: float | None = None
    consensus: str | None = None
