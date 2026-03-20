from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.config import Settings
from app.enrichment.llm_client import LLMClient
from app.enrichment.service import EnrichmentService


def _settings() -> Settings:
    return Settings(
        database_url="sqlite+aiosqlite:///test.db",
        serpapi_api_key="",
        theirstack_api_key="",
        apify_api_key="",
    )


def _fake_job(
    title: str = "Software Engineer",
    company: str = "Acme Inc",
    description_raw: str = (
        "<p>We need a <b>Python</b> developer"
        " with 5 years experience.</p>"
    ),
    **overrides,
) -> SimpleNamespace:
    """Fake job ORM-like object for enrichment tests."""
    defaults = {
        "id": "fake-123",
        "title": title,
        "company_name": company,
        "location": "New York, NY",
        "description_raw": description_raw,
        "description_clean": None,
        "description_markdown": None,
        "summary_ai": None,
        "skills_required": [],
        "skills_nice_to_have": [],
        "tech_stack": [],
        "red_flags": [],
        "green_flags": [],
        "salary_min": None,
        "salary_max": None,
        "salary_period": None,
        "experience_level": None,
        "seniority_score": None,
        "is_enriched": False,
        "enriched_at": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


LLM_RESPONSE = json.dumps(
    {
        "summary": "A Python developer role focused on backend services.",
        "skills_required": ["Python", "SQL", "REST APIs"],
        "skills_nice_to_have": ["Docker", "Kubernetes"],
        "tech_stack": ["Python", "PostgreSQL", "FastAPI"],
        "red_flags": [],
        "green_flags": ["Good work-life balance"],
        "experience_level": "mid",
        "seniority_score": 5,
        "salary_estimate": {"min": 120000, "max": 150000, "period": "annual"},
    }
)


class TestEnrichJob:
    @pytest.mark.asyncio
    async def test_full_enrichment_pipeline(self):
        llm = LLMClient(api_key="test-key")
        db = AsyncMock()
        svc = EnrichmentService(db, llm, _settings())

        job = _fake_job()

        with patch.object(llm, "chat", new_callable=AsyncMock, return_value=LLM_RESPONSE):
            result = await svc.enrich_job(job)

        assert result.is_enriched is True
        assert result.enriched_at is not None
        assert result.summary_ai == "A Python developer role focused on backend services."
        assert "Python" in result.skills_required
        assert "Docker" in result.skills_nice_to_have
        assert result.tech_stack == ["Python", "PostgreSQL", "FastAPI"]
        assert result.experience_level == "mid"
        assert result.seniority_score == 5

    @pytest.mark.asyncio
    async def test_salary_extracted_from_llm(self):
        llm = LLMClient(api_key="test-key")
        db = AsyncMock()
        svc = EnrichmentService(db, llm, _settings())

        job = _fake_job()

        with patch.object(llm, "chat", new_callable=AsyncMock, return_value=LLM_RESPONSE):
            result = await svc.enrich_job(job)

        assert result.salary_min == 120000
        assert result.salary_max == 150000
        assert result.salary_period == "annual"

    @pytest.mark.asyncio
    async def test_existing_salary_not_overwritten(self):
        llm = LLMClient(api_key="test-key")
        db = AsyncMock()
        svc = EnrichmentService(db, llm, _settings())

        job = _fake_job(salary_min=100000, salary_max=130000)

        with patch.object(llm, "chat", new_callable=AsyncMock, return_value=LLM_RESPONSE):
            result = await svc.enrich_job(job)

        # Should keep original values, not LLM's
        assert result.salary_min == 100000
        assert result.salary_max == 130000

    @pytest.mark.asyncio
    async def test_no_description_skips_enrichment(self):
        llm = LLMClient(api_key="test-key")
        db = AsyncMock()
        svc = EnrichmentService(db, llm, _settings())

        job = _fake_job(description_raw=None)

        result = await svc.enrich_job(job)

        assert result.is_enriched is False
        assert result.summary_ai is None

    @pytest.mark.asyncio
    async def test_empty_llm_response_graceful(self):
        llm = LLMClient(api_key="test-key")
        db = AsyncMock()
        svc = EnrichmentService(db, llm, _settings())

        job = _fake_job()

        with patch.object(llm, "chat", new_callable=AsyncMock, return_value=""):
            result = await svc.enrich_job(job)

        # Should still clean HTML even if LLM fails
        assert result.description_clean is not None
        assert result.is_enriched is True

    @pytest.mark.asyncio
    async def test_malformed_json_recovery(self):
        llm = LLMClient(api_key="test-key")
        db = AsyncMock()
        svc = EnrichmentService(db, llm, _settings())

        job = _fake_job()
        malformed = 'Here is the JSON: {"summary": "A role", "skills_required": ["Python"]}'

        with patch.object(llm, "chat", new_callable=AsyncMock, return_value=malformed):
            result = await svc.enrich_job(job)

        assert result.summary_ai == "A role"
        assert "Python" in result.skills_required


class TestCleanHtml:
    def test_strips_tags(self):
        llm = LLMClient(api_key="")
        db = AsyncMock()
        svc = EnrichmentService(db, llm, _settings())

        result = svc._clean_html("<p>Hello <b>World</b></p>")
        assert "<p>" not in result
        assert "<b>" not in result
        assert "Hello" in result
        assert "World" in result

    def test_preserves_text(self):
        llm = LLMClient(api_key="")
        db = AsyncMock()
        svc = EnrichmentService(db, llm, _settings())

        result = svc._clean_html("No HTML here")
        assert result == "No HTML here"


class TestHtmlToMarkdown:
    def test_converts_heading(self):
        llm = LLMClient(api_key="")
        db = AsyncMock()
        svc = EnrichmentService(db, llm, _settings())

        result = svc._html_to_markdown("<h1>Title</h1><p>Body</p>")
        assert "Title" in result
        assert "Body" in result

    def test_fallback_without_markdownify(self):
        llm = LLMClient(api_key="")
        db = AsyncMock()
        svc = EnrichmentService(db, llm, _settings())

        # Test the happy path — markdownify is installed
        result = svc._html_to_markdown("<p>text</p>")
        assert "text" in result
