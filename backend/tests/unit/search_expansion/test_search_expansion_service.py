"""Unit tests for SearchExpansionService."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.search_expansion.service import SearchExpansionService


class TestExpandQuery:
    @pytest.mark.asyncio
    async def test_returns_original_query(self):
        svc = SearchExpansionService(db=MagicMock())
        result = await svc.expand_query("python backend engineer")
        assert result["original_query"] == "python backend engineer"

    @pytest.mark.asyncio
    async def test_returns_expected_keys(self):
        svc = SearchExpansionService(db=MagicMock())
        result = await svc.expand_query("data scientist")
        assert "original_query" in result
        assert "expanded_terms" in result
        assert "synonyms" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_expanded_terms_is_list(self):
        svc = SearchExpansionService(db=MagicMock())
        result = await svc.expand_query("machine learning")
        assert isinstance(result["expanded_terms"], list)
        assert isinstance(result["synonyms"], list)

    @pytest.mark.asyncio
    async def test_empty_query_handled_gracefully(self):
        svc = SearchExpansionService(db=MagicMock())
        result = await svc.expand_query("")
        assert result["original_query"] == ""
        assert isinstance(result["expanded_terms"], list)

    @pytest.mark.asyncio
    async def test_message_indicates_pending_integration(self):
        svc = SearchExpansionService(db=MagicMock())
        result = await svc.expand_query("any query")
        assert result["message"]  # non-empty message
