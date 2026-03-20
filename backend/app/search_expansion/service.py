from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class SearchExpansionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def expand_query(self, query: str) -> dict:
        """Expand a search query with synonyms and related terms.

        Full LLM-powered expansion is a Phase 3B feature.
        """
        return {
            "original_query": query,
            "expanded_terms": [],
            "synonyms": [],
            "message": "Query expansion pending LLM integration",
        }
