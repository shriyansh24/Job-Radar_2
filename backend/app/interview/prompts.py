"""Prompt templates for interview preparation and evaluation.

Extracted from the monolithic ``service.py`` so they can be maintained
independently and reused by multiple modules.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Full interview-preparation bundle
# ---------------------------------------------------------------------------

INTERVIEW_PREP_PROMPT = """You are an expert interview coach.
Prepare this candidate for their interview.

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

# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

GENERATE_QUESTIONS_PROMPT = """You are an expert interview coach.
Generate {count} interview questions for the following job.

Return ONLY valid JSON:
{{
  "questions": [
    {{"type": "behavioral|technical|situational", "question": "..."}}
  ]
}}

RULES:
- Generate exactly {count} questions
- Question types should come from this set: {types}
- Make questions specific and realistic for the role
- Mix difficulty levels

JOB TITLE: {job_title}
COMPANY: {company_name}
JOB DESCRIPTION:
{job_description}
"""

# ---------------------------------------------------------------------------
# Answer evaluation
# ---------------------------------------------------------------------------

EVALUATE_ANSWER_PROMPT = """You are an expert interview coach. Evaluate this candidate's answer.

JOB TITLE: {job_title}
COMPANY: {company}

INTERVIEW QUESTION:
{question}

CANDIDATE'S ANSWER:
{answer}

Return ONLY valid JSON:
{{
  "score": <integer 1-10>,
  "feedback": "2-3 sentences of overall feedback",
  "strengths": ["strength1", "strength2"],
  "improvements": ["improvement1", "improvement2"]
}}

SCORING GUIDE:
- 9-10: Exceptional -- specific, well-structured, compelling examples
- 7-8: Strong -- relevant and clear but could add more detail
- 5-6: Adequate -- answers the question but lacks depth or specifics
- 3-4: Weak -- vague, off-topic, or missing key elements
- 1-2: Poor -- does not address the question
"""
