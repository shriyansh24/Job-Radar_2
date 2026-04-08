"""Unit tests for AIScraper."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.scraping.scrapers.ai_scraper import AIScraper


def _make_scraper(*, is_configured: bool = True) -> AIScraper:
    settings = MagicMock()
    llm = MagicMock()
    llm.is_configured = is_configured
    return AIScraper(settings=settings, llm_client=llm)


# ---------------------------------------------------------------------------
# _parse_llm_response (static method — pure logic)
# ---------------------------------------------------------------------------


class TestParseLlmResponse:
    def test_valid_json_array(self):
        raw = json.dumps([{"title": "Engineer", "company_name": "Acme", "url": "https://acme.com/jobs/1"}])
        result = AIScraper._parse_llm_response(raw, "https://example.com")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Engineer"

    def test_strips_markdown_fences(self):
        raw = "```json\n[{\"title\": \"Dev\", \"company_name\": \"Corp\"}]\n```"
        result = AIScraper._parse_llm_response(raw, "https://example.com")
        assert result is not None
        assert result[0]["title"] == "Dev"

    def test_empty_array(self):
        result = AIScraper._parse_llm_response("[]", "https://example.com")
        assert result == []

    def test_malformed_json_returns_none(self):
        result = AIScraper._parse_llm_response("{not valid json", "https://example.com")
        assert result is None

    def test_no_array_brackets_returns_none(self):
        result = AIScraper._parse_llm_response("some plain text response", "https://example.com")
        assert result is None

    def test_nested_object_not_array_returns_none(self):
        result = AIScraper._parse_llm_response('{"title": "Engineer"}', "https://example.com")
        assert result is None


# ---------------------------------------------------------------------------
# _prepare_html (static method — pure logic)
# ---------------------------------------------------------------------------


class TestPrepareHtml:
    def test_strips_script_tags(self):
        html = "<html><script>var x = 1;</script><p>Content</p></html>"
        cleaned = AIScraper._prepare_html(html)
        assert "var x" not in cleaned
        assert "Content" in cleaned

    def test_strips_style_tags(self):
        html = "<style>.cls { color: red; }</style><p>Text</p>"
        cleaned = AIScraper._prepare_html(html)
        assert ".cls" not in cleaned

    def test_truncates_to_max_chars(self):
        html = "a" * 100_000
        cleaned = AIScraper._prepare_html(html)
        assert len(cleaned) <= 8_000

    def test_collapses_whitespace(self):
        html = "<p>Word1     Word2</p>"
        cleaned = AIScraper._prepare_html(html)
        assert "  " not in cleaned


# ---------------------------------------------------------------------------
# _normalize_ai_job
# ---------------------------------------------------------------------------


class TestNormalizeAiJob:
    def test_returns_scraped_job_with_title(self):
        scraper = _make_scraper()
        raw = {"title": "Backend Engineer", "company_name": "TechCo", "url": "https://techco.com/jobs/1"}
        result = scraper._normalize_ai_job(raw, "https://techco.com")
        assert result is not None
        assert result.title == "Backend Engineer"
        assert result.company_name == "TechCo"

    def test_returns_none_when_title_missing(self):
        scraper = _make_scraper()
        result = scraper._normalize_ai_job({"company_name": "Acme"}, "https://acme.com")
        assert result is None

    def test_normalizes_remote_type(self):
        scraper = _make_scraper()
        raw = {"title": "Dev", "company_name": "Co", "remote_type": "REMOTE"}
        result = scraper._normalize_ai_job(raw, "https://co.com")
        assert result is not None
        assert result.remote_type == "remote"

    def test_unknown_remote_type_becomes_none(self):
        scraper = _make_scraper()
        raw = {"title": "Dev", "company_name": "Co", "remote_type": "maybe"}
        result = scraper._normalize_ai_job(raw, "https://co.com")
        assert result is not None
        assert result.remote_type is None

    def test_salary_fields_parsed(self):
        scraper = _make_scraper()
        raw = {"title": "Dev", "company_name": "Co", "salary_min": 100000, "salary_max": 150000}
        result = scraper._normalize_ai_job(raw, "https://co.com")
        assert result is not None
        assert result.salary_min == 100000.0
        assert result.salary_max == 150000.0
        assert result.salary_period == "annual"

    def test_invalid_salary_handled_gracefully(self):
        scraper = _make_scraper()
        raw = {"title": "Dev", "company_name": "Co", "salary_min": "not a number"}
        result = scraper._normalize_ai_job(raw, "https://co.com")
        assert result is not None
        assert result.salary_min is None

    def test_falls_back_to_page_url_when_no_job_url(self):
        scraper = _make_scraper()
        raw = {"title": "Dev", "company_name": "Co", "url": ""}
        result = scraper._normalize_ai_job(raw, "https://fallback.com")
        assert result is not None
        assert result.source_url == "https://fallback.com"


# ---------------------------------------------------------------------------
# fetch_from_url — integration with LLM mock
# ---------------------------------------------------------------------------


class TestFetchFromUrl:
    @pytest.mark.asyncio
    async def test_llm_not_configured_returns_empty(self):
        scraper = _make_scraper(is_configured=False)
        result = await scraper.fetch_from_url("https://jobs.example.com", html="<html>Jobs</html>")
        assert result == []

    @pytest.mark.asyncio
    async def test_llm_error_returns_empty(self):
        scraper = _make_scraper(is_configured=True)
        scraper._llm.chat = AsyncMock(side_effect=Exception("API error"))
        result = await scraper.fetch_from_url("https://jobs.example.com", html="<html>Jobs</html>")
        assert result == []

    @pytest.mark.asyncio
    async def test_successful_extraction_returns_jobs(self):
        scraper = _make_scraper(is_configured=True)
        payload = [{"title": "Dev", "company_name": "TechCo", "url": "https://techco.com/j/1"}]
        scraper._llm.chat = AsyncMock(return_value=json.dumps(payload))

        result = await scraper.fetch_from_url(
            "https://jobs.example.com", html="<html>Some job content</html>"
        )
        assert len(result) == 1
        assert result[0].title == "Dev"

    @pytest.mark.asyncio
    async def test_cache_hit_returns_same_results(self):
        scraper = _make_scraper(is_configured=True)
        payload = [{"title": "Dev", "company_name": "TechCo", "url": "https://techco.com/j/1"}]
        scraper._llm.chat = AsyncMock(return_value=json.dumps(payload))
        html = "<html>Cacheable content</html>"

        first = await scraper.fetch_from_url("https://jobs.example.com", html=html)
        second = await scraper.fetch_from_url("https://jobs.example.com", html=html)
        # LLM called only once
        assert scraper._llm.chat.call_count == 1
        assert len(first) == len(second)

    @pytest.mark.asyncio
    async def test_limit_respected(self):
        scraper = _make_scraper(is_configured=True)
        payload = [
            {"title": f"Job {i}", "company_name": "Co", "url": f"https://co.com/{i}"}
            for i in range(10)
        ]
        scraper._llm.chat = AsyncMock(return_value=json.dumps(payload))

        result = await scraper.fetch_from_url(
            "https://jobs.example.com", html="<html>jobs</html>", limit=3
        )
        assert len(result) == 3


# ---------------------------------------------------------------------------
# _safe_float
# ---------------------------------------------------------------------------


class TestSafeFloat:
    def test_none_returns_none(self):
        assert AIScraper._safe_float(None) is None

    def test_int_returns_float(self):
        assert AIScraper._safe_float(100) == 100.0

    def test_string_number_returns_float(self):
        assert AIScraper._safe_float("99.5") == 99.5

    def test_invalid_string_returns_none(self):
        assert AIScraper._safe_float("not a number") is None
