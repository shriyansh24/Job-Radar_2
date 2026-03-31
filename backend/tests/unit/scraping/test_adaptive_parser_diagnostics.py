from __future__ import annotations

from pathlib import Path

import pytest

from app.scraping.execution.escalation_engine import (
    EscalationReason,
    should_escalate,
)
from app.scraping.scrapers.adaptive_parser import AdaptiveCareerParser

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "career_pages"


def _fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("fixture_name", "expected_strategy", "expected_jobs", "expected_signal"),
    [
        ("generic_no_json_ld.html", "selector", 4, "selector_match"),
        ("generic_with_json_ld.html", "selector", 3, "selector_match"),
        ("json_ld_only.html", "json_ld", 2, "json_ld_match"),
        ("js_hydrated_jobs.html", "embedded_state", 2, "embedded_state_match"),
        ("js_heavy_blank.html", "js_shell_blank", 0, "js_shell"),
        ("cloudflare_challenge.html", "anti_bot_challenge", 0, "cloudflare"),
    ],
)
def test_adaptive_parser_diagnoses_fixture_strategy(
    fixture_name: str,
    expected_strategy: str,
    expected_jobs: int,
    expected_signal: str,
) -> None:
    parser = AdaptiveCareerParser(
        html=_fixture(fixture_name),
        company_name="FixtureCo",
        base_url="https://fixture.example/careers",
    )

    diagnosis = parser.diagnose()
    jobs = parser.extract()

    assert diagnosis.strategy == expected_strategy
    assert diagnosis.jobs_found == expected_jobs
    assert len(jobs) == expected_jobs
    assert expected_signal in diagnosis.signals


def test_cloudflare_fixture_maps_to_escalation_reason() -> None:
    html = _fixture("cloudflare_challenge.html")

    decision = should_escalate(
        status_code=403,
        jobs_found=0,
        html_length=len(html),
        html_snippet=html,
    )

    assert decision is not None
    assert decision.reason == EscalationReason.CLOUDFLARE_CHALLENGE
    assert decision.skip_to_tier == 2
