from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.interview.schemas import (
    EvaluateAnswerRequest,
    EvaluateAnswerResponse,
    GenerateQuestionsRequest,
    InterviewPrepRequest,
    InterviewPrepResponse,
    InterviewSessionResponse,
)
from app.interview.service import InterviewService

router = APIRouter(prefix="/interview", tags=["interview"])


@router.get("/sessions", response_model=list[InterviewSessionResponse])
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[InterviewSessionResponse]:
    svc = InterviewService(db)
    items = await svc.list_sessions(user.id)
    return [InterviewSessionResponse.model_validate(s) for s in items]


@router.get("/sessions/{session_id}", response_model=InterviewSessionResponse)
async def get_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewSessionResponse:
    svc = InterviewService(db)
    s = await svc.get_session(session_id, user.id)
    return InterviewSessionResponse.model_validate(s)


@router.post("/generate", response_model=InterviewSessionResponse, status_code=201)
async def generate_questions(
    data: GenerateQuestionsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewSessionResponse:
    svc = InterviewService(db)
    s = await svc.generate_questions(data, user.id)
    return InterviewSessionResponse.model_validate(s)


@router.post("/prepare", response_model=InterviewPrepResponse)
async def prepare_interview(
    data: InterviewPrepRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewPrepResponse:
    """Full interview-preparation bundle: likely questions, STAR stories,
    technical topics, company talking points, and red-flag responses."""
    svc = InterviewService(db)
    return await svc.prepare_interview(data, user.id)


@router.post("/evaluate", response_model=EvaluateAnswerResponse)
async def evaluate_answer(
    data: EvaluateAnswerRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvaluateAnswerResponse:
    svc = InterviewService(db)
    result = await svc.evaluate_answer(data, user.id)
    return EvaluateAnswerResponse(**result)
