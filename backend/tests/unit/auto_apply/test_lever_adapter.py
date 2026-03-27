from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.auto_apply.lever_adapter import ApplicationResult, LeverAPIAdapter


class TestParseUrl:
    def test_valid_lever_url(self) -> None:
        result = LeverAPIAdapter.parse_lever_url(
            "https://jobs.lever.co/acmecorp/abc12345-6789-0000-1111-222233334444"
        )
        assert result == ("acmecorp", "abc12345-6789-0000-1111-222233334444")

    def test_lever_url_with_apply_suffix(self) -> None:
        result = LeverAPIAdapter.parse_lever_url(
            "https://jobs.lever.co/acmecorp/abc12345-6789-0000-1111-222233334444/apply"
        )
        assert result == ("acmecorp", "abc12345-6789-0000-1111-222233334444")

    def test_non_lever_url_returns_none(self) -> None:
        assert LeverAPIAdapter.parse_lever_url("https://boards.greenhouse.io/foo/1234") is None


class TestBuildPayload:
    def test_full_profile(self) -> None:
        adapter = LeverAPIAdapter()
        payload = adapter._build_profile_payload(
            {
                "full_name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "+1-555-0100",
                "current_company": "Acme Corp",
                "linkedin_url": "https://linkedin.com/in/janedoe",
                "github_url": "https://github.com/janedoe",
            }
        )
        assert payload["name"] == "Jane Doe"
        assert payload["email"] == "jane@example.com"
        assert payload["phone"] == "+1-555-0100"
        assert payload["org"] == "Acme Corp"
        assert payload["urls[LinkedIn]"] == "https://linkedin.com/in/janedoe"

    def test_first_last_fallback(self) -> None:
        payload = LeverAPIAdapter()._build_profile_payload(
            {"first_name": "John", "last_name": "Smith", "email": "john@example.com"}
        )
        assert payload["name"] == "John Smith"


class TestApply:
    @pytest.mark.asyncio
    async def test_success_response(self) -> None:
        adapter = LeverAPIAdapter()
        response = httpx.Response(
            200,
            json={"ok": True, "applicationId": "app-123"},
            request=httpx.Request("POST", "https://api.lever.co/v0/postings/acme/p1/apply"),
        )

        with patch("app.auto_apply.lever_adapter.httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.post.return_value = response
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=False)
            client_cls.return_value = client

            result = await adapter.apply(
                company_slug="acme",
                posting_id="p1",
                profile={"full_name": "Jane Doe", "email": "jane@example.com"},
            )

        assert result.success is True
        assert result.response_data == {"ok": True, "applicationId": "app-123"}

    @pytest.mark.asyncio
    async def test_http_failure(self) -> None:
        adapter = LeverAPIAdapter()
        response = httpx.Response(
            400,
            text="Bad Request",
            request=httpx.Request("POST", "https://api.lever.co/v0/postings/acme/p1/apply"),
        )

        with patch("app.auto_apply.lever_adapter.httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.post.return_value = response
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=False)
            client_cls.return_value = client

            result = await adapter.apply(
                company_slug="acme",
                posting_id="p1",
                profile={"full_name": "Jane Doe"},
            )

        assert result.success is False
        assert "HTTP 400" in result.error

    @pytest.mark.asyncio
    async def test_timeout(self) -> None:
        adapter = LeverAPIAdapter()
        with patch("app.auto_apply.lever_adapter.httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.post.side_effect = httpx.TimeoutException("timed out")
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=False)
            client_cls.return_value = client

            result = await adapter.apply(
                company_slug="acme",
                posting_id="p1",
                profile={"full_name": "Jane Doe", "email": "jane@example.com"},
            )

        assert result.success is False
        assert result.error == "Request timed out"

    @pytest.mark.asyncio
    async def test_resume_file_attached(self, tmp_path) -> None:
        resume = tmp_path / "resume.pdf"
        resume.write_bytes(b"%PDF-1.4 fake content")
        adapter = LeverAPIAdapter()
        response = httpx.Response(
            200,
            json={"ok": True},
            request=httpx.Request("POST", "https://api.lever.co/v0/postings/acme/p1/apply"),
        )

        with patch("app.auto_apply.lever_adapter.httpx.AsyncClient") as client_cls:
            client = AsyncMock()
            client.post.return_value = response
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=False)
            client_cls.return_value = client

            result = await adapter.apply(
                company_slug="acme",
                posting_id="p1",
                profile={"full_name": "J D", "email": "jane@example.com"},
                resume_path=str(resume),
            )

        assert result.success is True
        assert "files" in client.post.call_args.kwargs


class TestApplicationResult:
    def test_defaults(self) -> None:
        result = ApplicationResult(success=True, ats="lever", method="api")
        assert result.error is None
        assert result.fields_filled == {}
        assert result.fields_missed == []
