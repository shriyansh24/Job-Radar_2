from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.rag import PersonalRAG
from app.auth.models import User
from app.config import settings
from app.copilot.schemas import (
    AskHistoryRequest,
    AskHistoryResponse,
    CopilotRequest,
    CoverLetterCreate,
    CoverLetterResponse,
)
from app.copilot.service import CopilotService
from app.dependencies import get_current_user, get_db
from app.enrichment.embedding import EmbeddingService
from app.enrichment.llm_client import LLMClient

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post("/chat")
async def copilot_chat(
    data: CopilotRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = CopilotService(db)
    chunks = []
    async for chunk in svc.chat(data.message, data.context, user.id):
        chunks.append(chunk)
    return {"response": "".join(chunks)}


@router.post("/ask-history", response_model=AskHistoryResponse)
async def ask_history(
    data: AskHistoryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AskHistoryResponse:
    embedder = EmbeddingService(db)
    llm = LLMClient(api_key=settings.openrouter_api_key, model=settings.default_llm_model)
    try:
        rag = PersonalRAG(db=db, embedder=embedder, llm=llm)
        answer = await rag.query(data.question, user.id)
        return AskHistoryResponse(answer=answer)
    finally:
        await llm.close()


@router.post("/cover-letter", response_model=CoverLetterResponse, status_code=201)
async def generate_cover_letter(
    data: CoverLetterCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CoverLetterResponse:
    svc = CopilotService(db)
    cl = await svc.generate_cover_letter(data.job_id, data.style, user.id, template=data.template)
    return CoverLetterResponse.model_validate(cl)
