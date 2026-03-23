"""Tests for the Lever API adapter."""

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

    def test_lever_url_with_path_suffix(self) -> None:
        result = LeverAPIAdapter.parse_lever_url(
            "https://jobs.lever.co/acmecorp/abc12345-6789-0000-1111-222233334444/apply"
        )
        assert result == ("acmecorp", "abc12345-6789-0000-1111-222233334444")

    def test_non_lever_url(self) -> None:
        assert LeverAPIAdapter.parse_lever_url("https://boards.greenhouse.io/foo/1234") is None

    def test_empty_url(self) -> None:
        assert LeverAPIAdapter.parse_lever_url("") is None


class TestBuildPayload:
    def test_full_profile(self) -> None:
        adapter = LeverAPIAdapter()
        profile = {
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+1-555-0100",
            "current_company": "Acme Corp",
            "linkedin_url": "https://linkedin.com/in/janedoe",
            "github_url": "https://github.com/janedoe",
        }
        data = adapter._build_profile_payload(profile)

        assert data["name"] == "Jane Doe"
        assert data["email"] == "jane@example.com"
        assert data["phone"] == "+1-555-0100"
        assert data["org"] == "Acme Corp"
        assert data["urls[LinkedIn]"] == "https://linkedin.com/in/janedoe"
        assert data["urls[GitHub]"] == "https://github.com/janedoe"

    def test_first_last_name_fallback(self) -> None:
        adapter = LeverAPIAdapter()
        profile = {"first_name": "John", "last_name": "Smith", "email": "j@x.com"}
        data = adapter._build_profile_payload(profile)
        assert data["name"] == "John Smith"

    def test_minimal_profile(self) -> None:
        adapter = LeverAPIAdapter()
        profile = {"email": "a@b.com"}
        data = adapter._build_profile_payload(profile)
        assert data["email"] == "a@b.com"
        assert data["name"] == ""
        assert "phone" not in data
        assert "org" not in data


class TestApply:
    @pytest.mark.asyncio
    async def test_success_response(self) -> None:
        adapter = LeverAPIAdapter()
        mock_response = httpx.Response(
            200,
            json={"ok": True, "applicationId": "app-123"},
            request=httpx.Request("POST", "https://api.lever.co/v0/postings/acme/p1/apply"),
        )

        with patch("app.auto_apply.lever_adapter.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await adapter.apply(
                company_slug="acme",
                posting_id="p1",
                profile={"full_name": "Jane Doe", "email": "jane@x.com"},
            )

        assert result.success is True
        assert result.ats == "lever"
        assert result.method == "api"
        assert result.response_data == {"ok": True, "applicationId": "app-123"}
        assert result.error is None

    @pytest.mark.asyncio
    async def test_400_failure(self) -> None:
        adapter = LeverAPIAdapter()
        mock_response = httpx.Response(
            400,
            text="Bad Request: missing required field 'email'",
            request=httpx.Request("POST", "https://api.lever.co/v0/postings/acme/p1/apply"),
        )

        with patch("app.auto_apply.lever_adapter.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

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

        with patch("app.auto_apply.lever_adapter.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("timed out")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await adapter.apply(
                company_slug="acme",
                posting_id="p1",
                profile={"full_name": "Jane Doe", "email": "j@x.com"},
            )

        assert result.success is False
        assert result.error == "Request timed out"

    @pytest.mark.asyncio
    async def test_with_resume(self, tmp_path) -> None:
        resume = tmp_path / "resume.pdf"
        resume.write_bytes(b"%PDF-1.4 fake content")

        adapter = LeverAPIAdapter()
        mock_response = httpx.Response(
            200,
            json={"ok": True},
            request=httpx.Request("POST", "https://api.lever.co/v0/postings/acme/p1/apply"),
        )

        with patch("app.auto_apply.lever_adapter.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await adapter.apply(
                company_slug="acme",
                posting_id="p1",
                profile={"full_name": "J D", "email": "j@x.com"},
                resume_path=str(resume),
            )

        assert result.success is True
        # Verify files were passed
        call_kwargs = mock_client.post.call_args
        assert "files" in call_kwargs.kwargs or len(call_kwargs.args) > 1

    @pytest.mark.asyncio
    async def test_with_cover_letter(self) -> None:
        adapter = LeverAPIAdapter()
        mock_response = httpx.Response(
            200,
            json={"ok": True},
            request=httpx.Request("POST", "https://api.lever.co/v0/postings/acme/p1/apply"),
        )

        with patch("app.auto_apply.lever_adapter.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await adapter.apply(
                company_slug="acme",
                posting_id="p1",
                profile={"full_name": "J D", "email": "j@x.com"},
                cover_letter="I am excited to apply...",
            )

        assert result.success is True
        call_kwargs = mock_client.post.call_args
        assert call_kwargs.kwargs["data"]["comments"] == "I am excited to apply..."

    @pytest.mark.asyncio
    async def test_custom_questions(self) -> None:
        adapter = LeverAPIAdapter()
        mock_response = httpx.Response(
            200,
            json={"ok": True},
            request=httpx.Request("POST", "https://api.lever.co/v0/postings/acme/p1/apply"),
        )

        with patch("app.auto_apply.lever_adapter.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await adapter.apply(
                company_slug="acme",
                posting_id="p1",
                profile={"full_name": "J D", "email": "j@x.com"},
                custom_questions={"cards[0][field0]": "Yes"},
            )

        assert result.success is True
        call_kwargs = mock_client.post.call_args
        assert call_kwargs.kwargs["data"]["cards[0][field0]"] == "Yes"


class TestApplicationResult:
    def test_defaults(self) -> None:
        r = ApplicationResult(success=True, ats="lever", method="api")
        assert r.error is None
        assert r.needs_confirmation is False
        assert r.fields_filled == {}
        assert r.fields_missed == []
        assert r.blocked_by is None
