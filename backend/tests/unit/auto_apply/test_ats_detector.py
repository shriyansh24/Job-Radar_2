from __future__ import annotations

import pytest

from app.auto_apply.ats_detector import ATSDetector


class TestATSDetectorURL:
    """Test URL-based ATS detection for all providers."""

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://boards.greenhouse.io/company/jobs/123", "greenhouse"),
            ("https://jobs.lever.co/company/abc-123", "lever"),
            ("https://company.myworkdayjobs.com/en-US/careers/job/123", "workday"),
            ("https://wd5.myworkdayjobs.com/company", "workday"),
            ("https://company.workday.com/apply", "workday"),
            ("https://jobs.ashbyhq.com/company/abc", "ashby"),
            ("https://company.icims.com/jobs/1234", "icims"),
            ("https://careers-company.icims.com/jobs", "icims"),
            ("https://company.taleo.net/careersection/apply", "taleo"),
            ("https://oracle.com/taleo/application", "taleo"),
            ("https://company.bamboohr.com/careers/123", "bamboohr"),
            ("https://company.applytojob.com/apply/abc", "jazz"),
            ("https://company.jazzhr.com/apply/abc", "jazz"),
            ("https://jobs.smartrecruiters.com/Company/abc", "smartrecruiters"),
            ("https://app.jobvite.com/j?cid=abc", "jobvite"),
        ],
    )
    def test_detect_known_ats(self, url: str, expected: str) -> None:
        assert ATSDetector.detect(url) == expected

    def test_detect_unknown_url(self) -> None:
        assert ATSDetector.detect("https://company.com/careers") is None

    def test_detect_empty_url(self) -> None:
        assert ATSDetector.detect("") is None

    def test_detect_case_insensitive(self) -> None:
        assert ATSDetector.detect("https://Boards.Greenhouse.IO/company") == "greenhouse"
        assert ATSDetector.detect("https://JOBS.LEVER.CO/company") == "lever"

    def test_all_providers_covered(self) -> None:
        """Ensure every provider in ATS_PATTERNS is tested."""
        providers = set(ATSDetector.ATS_PATTERNS.keys())
        assert providers == {
            "greenhouse",
            "lever",
            "workday",
            "ashby",
            "icims",
            "taleo",
            "bamboohr",
            "jazz",
            "smartrecruiters",
            "jobvite",
        }
