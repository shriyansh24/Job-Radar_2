"""Tests for WorkdayScraper ATS adapter."""
from __future__ import annotations

import pytest

from app.scraping.port import ScrapedJob, ScraperPort
from app.scraping.scrapers.workday import WorkdayScraper


MOCK_RESPONSE = {
    "total": 2,
    "jobPostings": [
        {
            "title": "ML Engineer",
            "locationsText": "Seattle, WA",
            "postedOn": "2026-03-15",
            "bulletFields": ["Full-time"],
            "externalPath": "/job/ML-Engineer/12345",
        },
        {
            "title": "Data Scientist",
            "locationsText": "Remote",
            "postedOn": "2026-03-14",
            "bulletFields": ["Full-time"],
            "externalPath": "/job/Data-Scientist/12346",
        },
    ],
}


def test_implements_scraper_port():
    assert issubclass(WorkdayScraper, ScraperPort)


def test_source_name():
    scraper = WorkdayScraper.__new__(WorkdayScraper)
    assert scraper.source_name == "workday"


def test_parse_workday_response():
    scraper = WorkdayScraper.__new__(WorkdayScraper)
    jobs = scraper._parse_response(
        MOCK_RESPONSE, "https://microsoft.wd5.myworkdayjobs.com"
    )
    assert len(jobs) == 2
    assert jobs[0].title == "ML Engineer"
    assert jobs[0].location == "Seattle, WA"
    assert jobs[0].source == "workday"
    assert jobs[0].company_name == "microsoft"
    assert jobs[0].job_type == "Full-time"
    assert "/job/ML-Engineer/12345" in (jobs[0].source_url or "")


def test_parse_workday_response_second_job():
    scraper = WorkdayScraper.__new__(WorkdayScraper)
    jobs = scraper._parse_response(
        MOCK_RESPONSE, "https://microsoft.wd5.myworkdayjobs.com"
    )
    assert jobs[1].title == "Data Scientist"
    assert jobs[1].location == "Remote"
    assert jobs[1].remote_type == "remote"


def test_parse_empty_response():
    scraper = WorkdayScraper.__new__(WorkdayScraper)
    jobs = scraper._parse_response(
        {"total": 0, "jobPostings": []},
        "https://microsoft.wd5.myworkdayjobs.com",
    )
    assert jobs == []


def test_parse_missing_fields():
    """Jobs with missing optional fields should still parse."""
    scraper = WorkdayScraper.__new__(WorkdayScraper)
    data = {
        "total": 1,
        "jobPostings": [
            {
                "title": "Test Role",
                "externalPath": "/job/Test/999",
            }
        ],
    }
    jobs = scraper._parse_response(
        data, "https://acme.wd1.myworkdayjobs.com"
    )
    assert len(jobs) == 1
    assert jobs[0].title == "Test Role"
    assert jobs[0].company_name == "acme"
    assert jobs[0].location is None
    assert jobs[0].job_type is None


def test_extract_tenant_from_url():
    scraper = WorkdayScraper.__new__(WorkdayScraper)
    result = scraper._extract_tenant(
        "https://microsoft.wd5.myworkdayjobs.com/en-US/Global"
    )
    assert result == ("microsoft", "wd5", "Global")


def test_extract_tenant_different_subdomain():
    scraper = WorkdayScraper.__new__(WorkdayScraper)
    result = scraper._extract_tenant(
        "https://amazon.wd5.myworkdayjobs.com/en-US/AmazonNew"
    )
    assert result == ("amazon", "wd5", "AmazonNew")


def test_extract_tenant_no_locale():
    """URL without locale prefix should still parse."""
    scraper = WorkdayScraper.__new__(WorkdayScraper)
    result = scraper._extract_tenant(
        "https://netflix.wd1.myworkdayjobs.com/NetflixJobs"
    )
    assert result == ("netflix", "wd1", "NetflixJobs")


def test_extract_tenant_uppercase_url():
    """Workday URLs should parse regardless of hostname casing."""
    scraper = WorkdayScraper.__new__(WorkdayScraper)
    result = scraper._extract_tenant(
        "https://NVIDIA.WD5.MYWORKDAYJOBS.COM/en-US/Careers"
    )
    assert result == ("NVIDIA", "WD5", "Careers")


def test_extract_tenant_invalid_url():
    scraper = WorkdayScraper.__new__(WorkdayScraper)
    with pytest.raises(ValueError, match="Not a valid Workday URL"):
        scraper._extract_tenant("https://example.com/jobs")


def test_parse_posted_date():
    scraper = WorkdayScraper.__new__(WorkdayScraper)
    jobs = scraper._parse_response(
        MOCK_RESPONSE, "https://microsoft.wd5.myworkdayjobs.com"
    )
    assert jobs[0].posted_at is not None
    assert jobs[0].posted_at.year == 2026
    assert jobs[0].posted_at.month == 3
    assert jobs[0].posted_at.day == 15


def test_build_api_url():
    scraper = WorkdayScraper.__new__(WorkdayScraper)
    url = scraper._build_api_url("microsoft", "wd5", "Global")
    assert url == "https://microsoft.wd5.myworkdayjobs.com/wday/cxs/microsoft/Global/jobs"


def test_build_payload_defaults():
    scraper = WorkdayScraper.__new__(WorkdayScraper)
    payload = scraper._build_payload(limit=20, offset=0)
    assert payload["limit"] == 20
    assert payload["offset"] == 0
    assert "searchText" not in payload


def test_build_payload_with_query():
    scraper = WorkdayScraper.__new__(WorkdayScraper)
    payload = scraper._build_payload(limit=20, offset=0, query="engineer")
    assert payload["searchText"] == "engineer"


def test_build_payload_with_location():
    scraper = WorkdayScraper.__new__(WorkdayScraper)
    payload = scraper._build_payload(
        limit=20, offset=0, location="Seattle"
    )
    assert any(
        loc.get("value") == "Seattle"
        for loc in payload.get("locations", [])
    )
