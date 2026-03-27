from __future__ import annotations

import pytest

from app.scraping.normalization import (
    CompanyNormalizer,
    LocationNormalizer,
    TitleNormalizer,
    TitleNormalizerStripped,
)


class TestCompanyNormalizer:
    norm = CompanyNormalizer()

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("Google LLC", "google"),
            ("Meta Platforms, Inc.", "meta"),
            ("Amazon.com, Inc.", "amazon"),
            ("Microsoft Corporation", "microsoft"),
            ("Acme Corp", "acme"),
            ("Siemens AG", "siemens"),
        ],
    )
    def test_basic(self, raw: str, expected: str) -> None:
        assert self.norm.normalize(raw) == expected

    def test_ampersand_preserved(self) -> None:
        assert self.norm.normalize("AT&T Inc.") == "at&t"

    def test_unicode_accent(self) -> None:
        assert self.norm.normalize("Z\u00fcrich Insurance Group") == "zurich insurance"


class TestTitleNormalizer:
    norm = TitleNormalizer()

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("Sr. ML Eng", "senior machine learning engineer"),
            ("Jr. SWE", "junior software engineer"),
            ("Staff PM", "staff product manager"),
        ],
    )
    def test_basic(self, raw: str, expected: str) -> None:
        assert self.norm.normalize(raw) == expected


class TestTitleNormalizerStripped:
    norm = TitleNormalizerStripped()

    def test_strips_level(self) -> None:
        assert self.norm.normalize("Senior Software Engineer III") == "software engineer"

    def test_strips_lead(self) -> None:
        assert self.norm.normalize("Lead Data Engineer") == "data engineer"


class TestLocationNormalizer:
    norm = LocationNormalizer()

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("SF", "san francisco"),
            ("NYC", "new york city"),
            ("San Francisco, CA", "san francisco ca"),
            ("Remote", "remote"),
        ],
    )
    def test_basic(self, raw: str, expected: str) -> None:
        assert self.norm.normalize(raw) == expected
