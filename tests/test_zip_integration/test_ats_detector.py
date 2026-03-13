"""Test ATS URL pattern detection."""
import pytest
from backend.adapters.ats_detector import detect_ats_provider, get_company_slug_from_url, build_api_url


class TestDetectATSProvider:
    def test_greenhouse(self):
        assert detect_ats_provider("https://boards.greenhouse.io/airbnb/jobs/123") == "greenhouse"

    def test_lever(self):
        assert detect_ats_provider("https://jobs.lever.co/stripe/abc-123") == "lever"

    def test_ashby(self):
        assert detect_ats_provider("https://jobs.ashbyhq.com/figma") == "ashby"

    def test_workday(self):
        assert detect_ats_provider("https://company.myworkdayjobs.com/en-US/external") == "workday"

    def test_linkedin(self):
        assert detect_ats_provider("https://www.linkedin.com/jobs/view/123456") == "linkedin"

    def test_indeed(self):
        assert detect_ats_provider("https://www.indeed.com/viewjob?jk=abc") == "indeed"

    def test_unknown_returns_none(self):
        assert detect_ats_provider("https://example.com/careers") is None

    def test_empty_url(self):
        assert detect_ats_provider("") is None

    def test_none_url(self):
        assert detect_ats_provider(None) is None

    def test_case_insensitive(self):
        assert detect_ats_provider("https://BOARDS.GREENHOUSE.IO/company") == "greenhouse"

    # --- Additional coverage for the other 9 providers ---

    def test_icims(self):
        assert detect_ats_provider("https://jobs.icims.com/jobs/1234/job") == "icims"

    def test_taleo(self):
        assert detect_ats_provider("https://acme.taleo.net/careersection/portal/jobdetail") == "taleo"

    def test_smartrecruiters(self):
        assert detect_ats_provider("https://jobs.smartrecruiters.com/Acme/12345") == "smartrecruiters"

    def test_jobvite(self):
        assert detect_ats_provider("https://jobs.jobvite.com/acme/job/abc123") == "jobvite"

    def test_breezyhr(self):
        assert detect_ats_provider("https://acme.breezy.hr/p/job-title") == "breezyhr"

    def test_jazz(self):
        assert detect_ats_provider("https://app.jazz.co/apply/acme/123") == "jazz"

    def test_bamboohr(self):
        assert detect_ats_provider("https://acme.bamboohr.com/jobs/view.php?id=42") == "bamboohr"

    def test_no_partial_match_on_unrelated(self):
        # Ensure "linkedin" suffix in an unrelated domain does not match
        assert detect_ats_provider("https://notlinkedin.com/profile") is None

    def test_url_with_query_string(self):
        # Query strings should not confuse pattern matching
        result = detect_ats_provider(
            "https://boards.greenhouse.io/stripe/jobs/4567?gh_src=1abc23"
        )
        assert result == "greenhouse"

    def test_url_with_fragment(self):
        result = detect_ats_provider(
            "https://jobs.lever.co/stripe/posting-id#apply"
        )
        assert result == "lever"


class TestGetCompanySlug:
    def test_greenhouse_slug(self):
        assert get_company_slug_from_url(
            "https://boards.greenhouse.io/airbnb/jobs/123", "greenhouse"
        ) == "airbnb"

    def test_lever_slug(self):
        assert get_company_slug_from_url(
            "https://jobs.lever.co/stripe", "lever"
        ) == "stripe"

    def test_ashby_slug(self):
        assert get_company_slug_from_url(
            "https://jobs.ashbyhq.com/figma", "ashby"
        ) == "figma"

    def test_empty_returns_none(self):
        assert get_company_slug_from_url("", "greenhouse") is None

    def test_none_url_returns_none(self):
        assert get_company_slug_from_url(None, "greenhouse") is None

    def test_unsupported_provider_returns_none(self):
        # workday, linkedin, etc. have no slug extraction
        assert get_company_slug_from_url(
            "https://company.myworkdayjobs.com/en-US/external", "workday"
        ) is None

    def test_greenhouse_slug_with_query(self):
        # Slug should stop at / or ?
        result = get_company_slug_from_url(
            "https://boards.greenhouse.io/openai?token=abc", "greenhouse"
        )
        assert result == "openai"

    def test_lever_slug_with_job_path(self):
        result = get_company_slug_from_url(
            "https://jobs.lever.co/anthropic/posting-id", "lever"
        )
        assert result == "anthropic"

    def test_ashby_slug_deep_path(self):
        result = get_company_slug_from_url(
            "https://jobs.ashbyhq.com/notion/abc-123/application", "ashby"
        )
        assert result == "notion"

    def test_wrong_provider_for_url(self):
        # Greenhouse URL with lever provider: pattern won't match
        assert get_company_slug_from_url(
            "https://boards.greenhouse.io/airbnb", "lever"
        ) is None


class TestBuildApiUrl:
    def test_greenhouse_api(self):
        url = build_api_url("greenhouse", "airbnb")
        assert "boards-api.greenhouse.io" in url
        assert "airbnb" in url

    def test_lever_api(self):
        url = build_api_url("lever", "stripe")
        assert "api.lever.co" in url
        assert "stripe" in url

    def test_ashby_api(self):
        url = build_api_url("ashby", "figma")
        assert "api.ashbyhq.com" in url
        assert "figma" in url

    def test_unknown_returns_none(self):
        assert build_api_url("workday", "company") is None

    def test_linkedin_returns_none(self):
        assert build_api_url("linkedin", "company") is None

    def test_greenhouse_full_url(self):
        url = build_api_url("greenhouse", "openai")
        assert url == "https://boards-api.greenhouse.io/v1/boards/openai/jobs?content=true"

    def test_lever_full_url(self):
        url = build_api_url("lever", "anthropic")
        assert url == "https://api.lever.co/v0/postings/anthropic?mode=json"

    def test_ashby_full_url(self):
        url = build_api_url("ashby", "notion")
        assert url == "https://api.ashbyhq.com/posting-api/job-board/notion?includeCompensation=true"

    def test_icims_returns_none(self):
        assert build_api_url("icims", "company") is None

    def test_slug_with_hyphen(self):
        url = build_api_url("greenhouse", "my-company")
        assert "my-company" in url
