"""Question-answering engine for application form custom questions.

Uses an LLM to generate context-aware answers for unknown form questions,
with caching and question-type classification.
"""

from __future__ import annotations

import hashlib
import re
from enum import Enum

import structlog

from app.enrichment.llm_client import LLMClient

logger = structlog.get_logger()


class QuestionType(str, Enum):
    YES_NO = "yes_no"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    NUMERIC = "numeric"
    UNKNOWN = "unknown"


_YES_NO_PATTERNS = re.compile(
    r"\b(are you|do you|have you|will you|can you|is this|did you|were you)\b",
    re.IGNORECASE,
)
_NUMERIC_PATTERNS = re.compile(
    r"\b(how many|how much|number of|years of|how long|what is your gpa|salary expectation)\b",
    re.IGNORECASE,
)
_ESSAY_PATTERNS = re.compile(
    r"\b(describe|explain|tell us|elaborate|provide an example|discuss|summarize|"
    r"why do you want|what excites|what motivates|how have you|how would you)\b",
    re.IGNORECASE,
)


def classify_question(question: str) -> QuestionType:
    """Heuristically classify a form question into a QuestionType."""
    if _YES_NO_PATTERNS.search(question):
        return QuestionType.YES_NO
    if _NUMERIC_PATTERNS.search(question):
        return QuestionType.NUMERIC
    if _ESSAY_PATTERNS.search(question):
        return QuestionType.ESSAY
    return QuestionType.SHORT_ANSWER


_SYSTEM_PROMPT = """You are an assistant that helps fill out job application forms.
Given a form question and the applicant's context (name, skills, experience, etc.),
produce a concise, professional, and accurate answer.

Guidelines:
- For yes/no questions: reply with only "Yes" or "No".
- For numeric questions: reply with only the number (e.g. "5").
- For short-answer questions: reply in 1-3 sentences, no more than 100 words.
- For essay questions: write 2-4 well-structured paragraphs (150-400 words).
- Never include placeholder text such as [COMPANY] or <NAME> — use the actual values.
- Write in first person from the applicant's perspective.
- Do not repeat the question in your answer.
"""


class QuestionEngine:
    """LLM-backed engine for answering job application form questions.

    Features:
    - Classifies question type (yes/no, short answer, essay, numeric).
    - Generates answers via LLM using applicant profile context.
    - Caches answers keyed by question type + normalised question text.
    """

    def __init__(self, llm_client: LLMClient, review_before_submit: bool = False) -> None:
        self._llm = llm_client
        self.review_before_submit = review_before_submit
        self._cache: dict[str, str] = {}
        self._pending_review: dict[str, str] = {}

    async def answer(self, question: str, context: dict) -> str:
        """Generate (or retrieve from cache) an answer to a form question."""
        question_type = classify_question(question)
        key = self._cache_key(question, question_type)

        if key in self._cache:
            return self._cache[key]

        answer_text = await self._generate_answer(question, question_type, context)
        self._cache[key] = answer_text

        if self.review_before_submit:
            self._pending_review[key] = answer_text

        return answer_text

    def get_pending_review(self) -> list[dict[str, str]]:
        return [{"question_key": k, "answer": v} for k, v in self._pending_review.items()]

    def clear_pending_review(self) -> None:
        self._pending_review.clear()

    @staticmethod
    def _cache_key(question: str, question_type: QuestionType) -> str:
        normalised = question.lower().strip()
        payload = f"{question_type.value}::{normalised}"
        return hashlib.sha256(payload.encode()).hexdigest()

    async def _generate_answer(
        self, question: str, question_type: QuestionType, context: dict
    ) -> str:
        context_text = self._format_context(context)
        user_message = (
            f"Applicant context:\n{context_text}\n\n"
            f"Question type: {question_type.value}\n"
            f"Question: {question}\n\n"
            "Please provide your answer."
        )

        try:
            answer_text = await self._llm.chat(
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=600,
                temperature=0.3,
            )
            return answer_text.strip()
        except Exception as exc:
            logger.error("question_engine.llm_failed", error=str(exc))
            return self._fallback_answer(question_type, context)

    @staticmethod
    def _format_context(context: dict) -> str:
        lines = []
        for key, value in context.items():
            if value is not None:
                human_key = key.replace("_", " ").title()
                lines.append(f"- {human_key}: {value}")
        return "\n".join(lines) if lines else "(no context provided)"

    @staticmethod
    def _fallback_answer(question_type: QuestionType, context: dict) -> str:
        if question_type == QuestionType.YES_NO:
            return "Yes"
        if question_type == QuestionType.NUMERIC:
            years = context.get("years_experience")
            return str(years) if years is not None else "3"
        name = context.get("full_name", "I")
        return (
            f"{name} am a motivated professional with relevant experience "
            "who is excited about this opportunity and committed to making "
            "a positive impact in this role."
        )
