"""Interview preparation and evaluation service.

Prompt templates live in ``prompts.py``; scoring logic in ``evaluator.py``.
"""
from __future__ import annotations

import uuid
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.enrichment.llm_client import LLMClient
from app.interview import evaluator as answer_evaluator
from app.interview.models import InterviewSession
from app.interview.prompts import GENERATE_QUESTIONS_PROMPT, INTERVIEW_PREP_PROMPT
from app.interview.schemas import (
    EvaluateAnswerRequest,
    GenerateQuestionsRequest,
    InterviewPrepRequest,
    InterviewPrepResponse,
)
from app.nlp.model_router import ModelRouter
from app.shared.errors import AppError, NotFoundError

logger = structlog.get_logger()
_JSON_SYSTEM = {"role": "system", "content": "Return ONLY valid JSON."}


def _build_router() -> ModelRouter:
    llm = LLMClient(settings.openrouter_api_key, settings.default_llm_model)
    return ModelRouter(llm)


class InterviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._router = _build_router()

    # -- sessions ----------------------------------------------------------

    async def list_sessions(self, user_id: uuid.UUID) -> list[InterviewSession]:
        logger.info("interview.list_sessions", user_id=str(user_id))
        query = (
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.created_at.desc())
        )
        return list((await self.db.scalars(query)).all())

    async def get_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> InterviewSession:
        logger.info("interview.get_session", session_id=str(session_id), user_id=str(user_id))
        query = select(InterviewSession).where(
            InterviewSession.id == session_id, InterviewSession.user_id == user_id,
        )
        session = await self.db.scalar(query)
        if session is None:
            raise NotFoundError(detail=f"Interview session {session_id} not found")
        return session

    # -- question generation -----------------------------------------------

    async def generate_questions(
        self, request: GenerateQuestionsRequest, user_id: uuid.UUID,
    ) -> InterviewSession:
        logger.info("interview.generate_questions", job_id=request.job_id, user_id=str(user_id))
        types = request.types or ["behavioral", "technical"]
        count = request.count or 5
        job_title, company_name, job_description = await self._load_job_context(request.job_id)

        prompt = GENERATE_QUESTIONS_PROMPT.format(
            count=count, types=", ".join(types),
            job_title=job_title, company_name=company_name,
            job_description=job_description[:3000],
        )
        messages = [_JSON_SYSTEM, {"role": "user", "content": prompt}]

        try:
            data = await self._router.complete_json(
                task="interview", messages=messages, temperature=0.3, max_tokens=2000,
            )
            questions = data.get("questions", [])
            logger.info("interview.questions_generated", count=len(questions), user_id=str(user_id))
        except RuntimeError as exc:
            logger.exception("interview.generate_questions_failed", user_id=str(user_id))
            raise AppError("Question generation failed", status_code=502) from exc

        session = InterviewSession(
            user_id=user_id, job_id=request.job_id,
            questions=questions, answers=[], scores=[],
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    # -- interview prep ----------------------------------------------------

    async def prepare_interview(
        self, request: InterviewPrepRequest, user_id: uuid.UUID,
    ) -> InterviewPrepResponse:
        logger.info("interview.prepare", job_id=request.job_id, user_id=str(user_id))
        resume_text = request.resume_text.strip()
        if not resume_text:
            raise ValueError("Resume text is required for interview preparation")

        job_title, company_name = request.job_title, request.company_name
        job_description, required_skills = request.job_description, request.required_skills

        if not job_title:
            db_title, db_company, db_desc = await self._load_job_context(request.job_id)
            job_title = job_title or db_title
            company_name = company_name or db_company
            job_description = job_description or db_desc

        prompt = INTERVIEW_PREP_PROMPT.format(
            resume_text=resume_text[:4000], job_title=job_title,
            company_name=company_name or "the company",
            job_description=(job_description or "")[:3000],
            required_skills=", ".join(required_skills) if required_skills else "",
        )
        messages = [_JSON_SYSTEM, {"role": "user", "content": prompt}]

        data = await self._router.complete_json(
            task="interview", messages=messages, temperature=0.3, max_tokens=2500,
        )
        logger.info("interview.prepare_done", user_id=str(user_id))
        _keys = (
            "likely_questions", "star_stories", "technical_topics",
            "company_talking_points", "questions_to_ask", "red_flag_responses",
        )
        return InterviewPrepResponse(**{k: data.get(k, []) for k in _keys})

    # -- answer evaluation (delegates to evaluator) -------------------------

    async def evaluate_answer(self, request: EvaluateAnswerRequest, user_id: uuid.UUID) -> dict:
        logger.info(
            "interview.evaluate_answer", session_id=str(request.session_id),
            question_index=request.question_index, user_id=str(user_id),
        )
        session = await self.get_session(request.session_id, user_id)
        questions = session.questions or []
        if request.question_index < 0 or request.question_index >= len(questions):
            raise ValueError(
                f"question_index {request.question_index} out of range "
                f"(session has {len(questions)} questions)"
            )

        question_text = questions[request.question_index].get("question", "")
        job_title, company_name, _ = await self._load_job_context(session.job_id or "")

        result = await answer_evaluator.evaluate_answer(
            self._router,
            job_title=job_title, company=company_name,
            question_text=question_text, answer_text=request.answer,
        )
        await self._persist_score(session, request.question_index, request.answer, result)

        logger.info(
            "interview.evaluate_answer_done",
            score=result["score"], overall=str(session.overall_score),
            user_id=str(user_id),
        )
        return result

    # -- helpers -----------------------------------------------------------

    async def _persist_score(
        self, session: InterviewSession, question_index: int, answer: str, result: dict,
    ) -> None:
        idx = question_index
        answers = [a for a in list(session.answers or []) if a.get("question_index") != idx]
        scores = [s for s in list(session.scores or []) if s.get("question_index") != idx]
        answers.append({"question_index": idx, "answer": answer})
        scores.append({"question_index": idx, **result})

        session.answers = answers
        session.scores = scores
        numeric = [s["score"] for s in scores if isinstance(s.get("score"), (int, float))]
        if numeric:
            session.overall_score = round(sum(numeric) / len(numeric), 2)
        await self.db.commit()
        await self.db.refresh(session)

    async def _load_job_context(self, job_id: str) -> tuple[str, str, str]:
        if not job_id:
            return "", "", ""
        try:
            from app.jobs.models import Job
            job = await self.db.scalar(select(Job).where(Job.id == job_id))
            if job is None:
                return "", "", ""
            return (
                getattr(job, "title", "") or "",
                getattr(job, "company", "") or "",
                getattr(job, "description_clean", "") or getattr(job, "description", "") or "",
            )
        except Exception:
            logger.debug("interview.load_job_context_failed", job_id=job_id)
            return "", "", ""
