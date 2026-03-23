from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------


class GenerateQuestionsRequest(BaseModel):
    job_id: str
    count: int = 5
    types: list[str] | None = None  # behavioral, technical, system_design, culture_fit


# ---------------------------------------------------------------------------
# Full interview prep bundle
# ---------------------------------------------------------------------------


class InterviewPrepRequest(BaseModel):
    """Input for the full interview-preparation endpoint."""

    job_id: str
    resume_text: str = Field(..., min_length=50, description="Plain-text resume content")
    job_title: str = ""
    company_name: str = ""
    job_description: str = ""
    required_skills: list[str] = []


class StarStory(BaseModel):
    situation: str
    task: str
    action: str
    result: str


class LikelyQuestion(BaseModel):
    question: str
    category: str  # behavioral | technical | situational


class RedFlagResponse(BaseModel):
    question: str
    avoid: str
    instead: str


class InterviewPrepResponse(BaseModel):
    """Full interview-preparation bundle returned by the LLM."""

    likely_questions: list[LikelyQuestion] = []
    star_stories: list[StarStory] = []
    technical_topics: list[str] = []
    company_talking_points: list[str] = []
    questions_to_ask: list[str] = []
    red_flag_responses: list[RedFlagResponse] = []


# ---------------------------------------------------------------------------
# Answer evaluation
# ---------------------------------------------------------------------------


class EvaluateAnswerRequest(BaseModel):
    session_id: uuid.UUID
    question_index: int
    answer: str


class EvaluateAnswerResponse(BaseModel):
    score: float
    feedback: str
    strengths: list[str] = []
    improvements: list[str] = []


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


class InterviewSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: str | None = None
    questions: list[dict] = []
    answers: list[dict] = []
    scores: list[dict] = []
    overall_score: Decimal | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Contextual prep (stage-aware, application-linked)
# ---------------------------------------------------------------------------

VALID_PREP_STAGES = ("phone_screen", "technical", "behavioral", "final", "general")


class CompanyResearch(BaseModel):
    overview: str = ""
    recent_news: list[str] = []
    culture_values: list[str] = []
    interview_style: str = ""


class RoleAnalysis(BaseModel):
    key_requirements: list[str] = []
    skill_gaps: list[str] = []
    talking_points: list[str] = []
    seniority_expectations: str = ""


class PrepQuestion(BaseModel):
    question: str
    category: str = "general"
    why_likely: str = ""
    suggested_approach: str = ""


class StarResponse(BaseModel):
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""


class SuggestedAnswer(BaseModel):
    question: str
    star_response: StarResponse = Field(default_factory=StarResponse)
    key_points: list[str] = []


class QuestionToAsk(BaseModel):
    question: str
    why_effective: str = ""
    what_to_listen_for: str = ""


class PrepRedFlag(BaseModel):
    trap: str
    why_dangerous: str = ""
    better_approach: str = ""


class ContextualPrepData(BaseModel):
    company_research: CompanyResearch = Field(default_factory=CompanyResearch)
    role_analysis: RoleAnalysis = Field(default_factory=RoleAnalysis)
    likely_questions: list[PrepQuestion] = []
    suggested_answers: list[SuggestedAnswer] = []
    questions_to_ask: list[QuestionToAsk] = []
    red_flags: list[PrepRedFlag] = []


class ContextualPrepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    stage: str
    prep_data: ContextualPrepData
    created_at: datetime
    updated_at: datetime


class ContextualPrepRequest(BaseModel):
    stage: str = "general"

    @classmethod
    def validate_stage(cls, v: str) -> str:
        if v not in VALID_PREP_STAGES:
            raise ValueError(f"Invalid stage: {v}. Must be one of {VALID_PREP_STAGES}")
        return v
