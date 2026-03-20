from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.dependencies import get_current_user, get_db
from app.search_expansion.service import SearchExpansionService

router = APIRouter(prefix="/search-expansion", tags=["search_expansion"])


@router.post("/expand")
async def expand_query(
    data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    svc = SearchExpansionService(db)
    return await svc.expand_query(data.get("query", ""))
