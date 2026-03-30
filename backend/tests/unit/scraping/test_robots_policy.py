from __future__ import annotations

import pytest

from app.scraping.execution.robots_policy import evaluate_robots


class _Response:
    def __init__(self, status_code: int, text: str) -> None:
        self.status_code = status_code
        self.text = text


class _AsyncClient:
    def __init__(self, response: _Response | Exception) -> None:
        self._response = response

    async def __aenter__(self) -> "_AsyncClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def get(self, url: str, headers: dict[str, str]) -> _Response:
        _ = (url, headers)
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


@pytest.mark.asyncio
async def test_evaluate_robots_allows_missing_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.scraping.execution.robots_policy.httpx.AsyncClient",
        lambda **kwargs: _AsyncClient(_Response(404, "")),
    )
    decision = await evaluate_robots(
        "https://example.com/jobs",
        "JobRadar/1.0",
        {},
    )
    assert decision.allowed is True
    assert decision.reason == "robots_missing"


@pytest.mark.asyncio
async def test_evaluate_robots_blocks_disallowed_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.scraping.execution.robots_policy.httpx.AsyncClient",
        lambda **kwargs: _AsyncClient(
            _Response(
                200,
                "User-agent: *\nDisallow: /jobs\n",
            )
        ),
    )
    decision = await evaluate_robots(
        "https://example.com/jobs",
        "JobRadar/1.0",
        {},
    )
    assert decision.allowed is False
    assert decision.reason == "robots_disallowed"


@pytest.mark.asyncio
async def test_evaluate_robots_allows_when_fetch_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.scraping.execution.robots_policy.httpx.AsyncClient",
        lambda **kwargs: _AsyncClient(RuntimeError("network down")),
    )
    decision = await evaluate_robots(
        "https://example.com/jobs",
        "JobRadar/1.0",
        {},
    )
    assert decision.allowed is True
    assert decision.reason == "robots_unavailable"
