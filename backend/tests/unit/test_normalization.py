"""Tests for Feature A2: Company / Title / Location normalization."""

from __future__ import annotations

import pytest

from app.scraping.normalization import (
    CompanyNormalizer,
    LocationNormalizer,
    TitleNormalizer,
    TitleNormalizerStripped,
)

# ---------------------------------------------------------------------------
# CompanyNormalizer
# ---------------------------------------------------------------------------

class TestCompanyNormalizer:
    norm = CompanyNormalizer()

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("Google LLC", "google"),
            ("Meta Platforms, Inc.", "meta"),
            ("Amazon.com, Inc.", "amazon"),
            ("Stripe, Inc.", "stripe"),
            ("Microsoft Corporation", "microsoft"),
            ("Acme Corp", "acme"),
            ("  SpaceX  ", "spacex"),
            ("Siemens AG", "siemens"),
            ("SAP SE", "sap se"),  # SE is not in suffix list
            ("NVIDIA Corporation", "nvidia"),
        ],
    )
    def test_basic(self, raw: str, expected: str) -> None:
        assert self.norm.normalize(raw) == expected

    def test_empty_string(self) -> None:
        assert self.norm.normalize("") == ""

    def test_none(self) -> None:
        assert self.norm.normalize(None) == ""

    def test_ampersand_preserved(self) -> None:
        result = self.norm.normalize("AT&T Inc.")
        assert "at&t" == result

    def test_unicode_accent(self) -> None:
        # e.g. Zurich with an umlaut
        assert self.norm.normalize("Z\u00fcrich Insurance Group") == "zurich insurance"

    def test_multiple_suffixes(self) -> None:
        assert self.norm.normalize("Acme Technologies Corp") == "acme"


# ---------------------------------------------------------------------------
# TitleNormalizer
# ---------------------------------------------------------------------------

class TestTitleNormalizer:
    norm = TitleNormalizer()

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("Sr. ML Eng", "senior machine learning engineer"),
            ("Jr. SWE", "junior software engineer"),
            ("Staff PM", "staff product manager"),
            ("Data Scientist", "data scientist"),
            ("Mgr, Engineering", "manager engineering"),
        ],
    )
    def test_basic(self, raw: str, expected: str) -> None:
        assert self.norm.normalize(raw) == expected

    def test_empty_string(self) -> None:
        assert self.norm.normalize("") == ""

    def test_none(self) -> None:
        assert self.norm.normalize(None) == ""


class TestTitleNormalizerStripped:
    norm = TitleNormalizerStripped()

    def test_strips_level(self) -> None:
        result = self.norm.normalize("Senior Software Engineer III")
        # 'senior' and 'iii' are both level indicators
        assert result == "software engineer"

    def test_strips_lead(self) -> None:
        result = self.norm.normalize("Lead Data Engineer")
        assert result == "data engineer"


# ---------------------------------------------------------------------------
# LocationNormalizer
# ---------------------------------------------------------------------------

class TestLocationNormalizer:
    norm = LocationNormalizer()

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("SF", "san francisco"),
            ("NYC", "new york city"),
            ("sf", "san francisco"),
            ("San Francisco, CA", "san francisco ca"),
            ("Remote", "remote"),
        ],
    )
    def test_basic(self, raw: str, expected: str) -> None:
        assert self.norm.normalize(raw) == expected

    def test_empty_string(self) -> None:
        assert self.norm.normalize("") == ""

    def test_none(self) -> None:
        assert self.norm.normalize(None) == ""
