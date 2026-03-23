from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Tier 1: regex patterns for common form fields
# ---------------------------------------------------------------------------

_TIER1_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "first_name": [re.compile(r"first[\s_-]*name", re.I)],
    "last_name": [re.compile(r"last[\s_-]*name|surname", re.I)],
    "full_name": [re.compile(r"full[\s_-]*name|your[\s_-]*name", re.I)],
    "email": [re.compile(r"e[\s_-]*mail", re.I)],
    "phone": [re.compile(r"phone|mobile|cell", re.I)],
    "linkedin": [re.compile(r"linkedin", re.I)],
    "github": [re.compile(r"github", re.I)],
    "portfolio": [re.compile(r"portfolio|website|personal[\s_-]*site", re.I)],
    "resume": [re.compile(r"resume|cv|curriculum", re.I)],
    "cover_letter": [re.compile(r"cover[\s_-]*letter", re.I)],
    "location": [re.compile(r"location|city|address", re.I)],
    "salary_expectation": [re.compile(r"salary|compensation|pay[\s_-]*expect", re.I)],
    "work_authorization": [
        re.compile(r"authorized|work[\s_-]*auth|visa|sponsorship", re.I),
    ],
    "start_date": [re.compile(r"start[\s_-]*date|available[\s_-]*from|earliest", re.I)],
    "years_experience": [re.compile(r"years?.{0,10}experience", re.I)],
}


class FieldMapper:
    """3-tier field classification: regex -> DB lookup -> LLM (stub)."""

    def __init__(self, db: "AsyncSession | None" = None, ats_provider: str = "generic") -> None:
        self._db = db
        self._ats_provider = ats_provider

    async def classify(self, field_label: str) -> str | None:
        """Return the semantic key for a field label, or None if unknown."""
        result = self._classify_tier1(field_label)
        if result is not None:
            return result

        result = await self._classify_tier2(field_label)
        if result is not None:
            return result

        # Tier 3: LLM classification (future)
        return None

    def _classify_tier1(self, field_label: str) -> str | None:
        """Regex-based classification."""
        for semantic_key, patterns in _TIER1_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(field_label):
                    return semantic_key
        return None

    async def _classify_tier2(self, field_label: str) -> str | None:
        """DB lookup from learned mappings."""
        if self._db is None:
            return None

        from app.auto_apply.form_learning import FormLearningService

        svc = FormLearningService(self._db)
        return await svc.lookup_mapping(self._ats_provider, field_label)
