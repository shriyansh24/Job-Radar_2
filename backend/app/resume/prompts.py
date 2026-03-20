"""Prompt templates for the 3-stage resume tailoring pipeline and council evaluation.

Extracted from the monolithic ``service.py`` for readability and reuse.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Stage 1 — Job-description analysis
# ---------------------------------------------------------------------------

STAGE1_PROMPT = """Analyze this job description and extract structured requirements.

JOB TITLE: {job_title}
JOB DESCRIPTION:
{job_description}

Return ONLY valid JSON:
{{
  "hard_requirements": ["req1", "req2"],
  "soft_requirements": ["req1", "req2"],
  "key_technologies": ["tech1", "tech2"],
  "ats_keywords": ["keyword1", "keyword2"],
  "culture_signals": ["signal1", "signal2"],
  "seniority_indicators": ["indicator1"],
  "deal_breakers": ["requirement that must be met"]
}}
"""

# ---------------------------------------------------------------------------
# Stage 2 — Gap mapping (resume vs. requirements)
# ---------------------------------------------------------------------------

STAGE2_PROMPT = """Compare this resume against the job requirements and identify gaps.

RESUME:
{resume_text}

JOB REQUIREMENTS (from analysis):
Hard requirements: {hard_requirements}
Soft requirements: {soft_requirements}
Key technologies: {key_technologies}
ATS keywords: {ats_keywords}

Return ONLY valid JSON:
{{
  "matched_requirements": ["req1", "req2"],
  "partial_matches": [{{"requirement": "...", "evidence": "...", "gap": "..."}}],
  "missing_requirements": ["req1", "req2"],
  "transferable_skills": ["skill1", "skill2"],
  "keyword_coverage": {{"present": ["kw1"], "missing": ["kw2"]}},
  "strength_areas": ["area1"],
  "risk_areas": ["area1"]
}}
"""

# ---------------------------------------------------------------------------
# Stage 3 — Keyword injection / resume rewrite
# ---------------------------------------------------------------------------

STAGE3_PROMPT = """Rewrite this resume for the target job. Use the gap analysis to inject missing keywords
where the candidate has relevant experience. Never fabricate experience.

RESUME:
{resume_text}

MISSING KEYWORDS TO INJECT: {missing_keywords}
MATCHED STRENGTHS: {matched_requirements}
PARTIAL MATCHES TO STRENGTHEN: {partial_matches}

Return ONLY valid JSON:
{{
  "summary": "2-3 sentence professional summary tailored to this role",
  "reordered_experience": [{{"company": "...", "bullets": ["..."]}}],
  "enhanced_bullets": [{{"original": "...", "enhanced": "..."}}],
  "skills_section": ["skill1", "skill2"],
  "ats_score_before": 0-100,
  "ats_score_after": 0-100
}}
"""

# ---------------------------------------------------------------------------
# Council evaluation prompt
# ---------------------------------------------------------------------------

COUNCIL_PROMPT = """You are an expert resume reviewer. Evaluate this resume for the given job.

RESUME:
{resume_text}

JOB TITLE: {job_title}
JOB DESCRIPTION:
{job_description}

Score the resume from 0-100 on:
- Relevance to the job
- ATS keyword optimization
- Clarity and impact of bullet points
- Overall presentation

Return ONLY valid JSON:
{{
  "score": 0-100,
  "feedback": "2-3 sentence overall assessment",
  "strengths": ["strength1", "strength2"],
  "weaknesses": ["weakness1", "weakness2"]
}}
"""
