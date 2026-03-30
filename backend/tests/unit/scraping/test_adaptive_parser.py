from __future__ import annotations

from pathlib import Path

from app.scraping.scrapers.adaptive_parser import AdaptiveCareerParser

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "career_pages"


def _fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def test_adaptive_parser_extracts_job_cards() -> None:
    parser = AdaptiveCareerParser(
        html=_fixture("generic_no_json_ld.html"),
        company_name="TechStartup Inc",
        base_url="https://example.com/careers",
    )

    jobs = parser.extract()

    assert len(jobs) == 4
    assert jobs[0]["title"] == "Frontend Engineer"
    assert jobs[0]["url"] == "https://example.com/jobs/ts-001/apply"


def test_adaptive_parser_returns_no_jobs_for_js_shell() -> None:
    parser = AdaptiveCareerParser(
        html=_fixture("js_heavy_blank.html"),
        company_name="DynamicCo",
        base_url="https://example.com/careers",
    )

    assert parser.extract() == []
