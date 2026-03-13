"""Test BaseScraper new methods."""
import pytest
from backend.scrapers.base import BaseScraper


class TestExtractTechStack:
    def test_extracts_common_tech(self):
        desc = "We use Python, React, AWS, and PostgreSQL daily."
        result = BaseScraper.extract_tech_stack(desc)
        assert "Python" in result
        assert "React" in result
        assert "AWS" in result
        assert "PostgreSQL" in result

    def test_case_insensitive(self):
        desc = "Experience with PYTHON and javascript required."
        result = BaseScraper.extract_tech_stack(desc)
        assert len(result) >= 2

    def test_empty_description(self):
        assert BaseScraper.extract_tech_stack("") == []

    def test_no_tech_found(self):
        assert BaseScraper.extract_tech_stack("We sell cookies.") == []

    def test_max_15_results(self):
        desc = "Python Java C++ Go Rust Ruby PHP Swift Kotlin Scala TypeScript JavaScript React Angular Vue Django Flask FastAPI Spring Rails"
        result = BaseScraper.extract_tech_stack(desc)
        assert len(result) <= 15


class TestInferSeniority:
    def test_senior_engineer(self):
        assert BaseScraper._infer_seniority("Senior Software Engineer") == "senior"

    def test_staff_engineer(self):
        assert BaseScraper._infer_seniority("Staff ML Engineer") == "staff"

    def test_intern(self):
        assert BaseScraper._infer_seniority("Engineering Intern") == "intern"

    def test_junior_maps_to_entry(self):
        assert BaseScraper._infer_seniority("Junior Developer") == "entry"

    def test_lead(self):
        assert BaseScraper._infer_seniority("Lead Data Scientist") == "lead"

    def test_principal(self):
        assert BaseScraper._infer_seniority("Principal Engineer") == "principal"

    def test_vp_maps_to_exec(self):
        assert BaseScraper._infer_seniority("VP of Engineering") == "exec"

    def test_no_seniority_returns_none(self):
        assert BaseScraper._infer_seniority("Software Engineer") is None

    def test_case_insensitive(self):
        assert BaseScraper._infer_seniority("SENIOR ENGINEER") == "senior"


class TestNormalizeSalary:
    def test_hourly_to_annual(self):
        min_val, max_val = BaseScraper._normalize_salary(50, 75, "hourly")
        assert min_val == 50 * 2080
        assert max_val == 75 * 2080

    def test_annual_unchanged(self):
        min_val, max_val = BaseScraper._normalize_salary(100000, 150000, "year")
        assert min_val == 100000
        assert max_val == 150000

    def test_cents_to_dollars(self):
        min_val, max_val = BaseScraper._normalize_salary(10000000, 15000000, "year")
        assert min_val == 100000
        assert max_val == 150000

    def test_none_values(self):
        min_val, max_val = BaseScraper._normalize_salary(None, None, "year")
        assert min_val is None
        assert max_val is None
