from __future__ import annotations

import pytest

from app.scraping.scrapers.ashby import AshbyScraper
from app.scraping.scrapers.greenhouse import GreenhouseScraper
from app.scraping.scrapers.lever import LeverScraper
from app.scraping.scrapers.workday import WorkdayScraper


class _FakeResponse:
    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("unexpected status")

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, response: _FakeResponse):
        self.response = response

    async def get(self, *args, **kwargs):
        return self.response

    async def post(self, *args, **kwargs):
        return self.response


def _scraper(cls, payload):
    scraper = cls.__new__(cls)
    scraper._client = _FakeClient(_FakeResponse(payload))
    return scraper


@pytest.mark.asyncio
async def test_greenhouse_rejects_non_dict_payload():
    scraper = _scraper(GreenhouseScraper, [])

    jobs = await scraper.fetch_jobs("test")

    assert jobs == []


@pytest.mark.asyncio
async def test_lever_rejects_non_list_payload():
    scraper = _scraper(LeverScraper, {})

    jobs = await scraper.fetch_jobs("test")

    assert jobs == []


@pytest.mark.asyncio
async def test_ashby_errors_payload_returns_empty_list():
    scraper = _scraper(AshbyScraper, {"errors": [{"message": "boom"}]})

    jobs = await scraper.fetch_jobs("test")

    assert jobs == []


@pytest.mark.asyncio
async def test_workday_rejects_non_dict_payload():
    scraper = _scraper(WorkdayScraper, [])
    scraper._extract_tenant = lambda url: ("tenant", "wd5", "jobs")
    scraper._build_api_url = lambda tenant, subdomain, section: "https://example.com/jobs"

    jobs = await scraper.fetch_jobs("https://tenant.wd5.myworkdayjobs.com/en-US/jobs")

    assert jobs == []
