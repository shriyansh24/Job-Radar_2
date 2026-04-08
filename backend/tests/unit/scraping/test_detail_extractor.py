"""Unit tests for DetailPageExtractor."""

from __future__ import annotations

import json

from app.scraping.scrapers.detail_extractor import DetailPageExtractor

# ---------------------------------------------------------------------------
# JSON-LD extraction path
# ---------------------------------------------------------------------------


class TestJsonLdExtraction:
    def _make_jsonld_html(self, data: dict) -> str:
        return f"""
        <html>
        <head>
          <script type="application/ld+json">{json.dumps(data)}</script>
        </head>
        <body></body>
        </html>
        """

    def test_extracts_description_from_json_ld(self):
        data = {
            "@type": "JobPosting",
            "description": "We need a great engineer to build awesome systems.",
        }
        html = self._make_jsonld_html(data)
        result = DetailPageExtractor.extract(html)
        assert result["description_raw"] == "We need a great engineer to build awesome systems."

    def test_extracts_salary_from_json_ld(self):
        data = {
            "@type": "JobPosting",
            "description": "Great role.",
            "baseSalary": {
                "value": {"minValue": 100000, "maxValue": 150000},
                "unitText": "YEAR",
            },
        }
        html = self._make_jsonld_html(data)
        result = DetailPageExtractor.extract(html)
        assert result["salary_min"] == 100000
        assert result["salary_max"] == 150000
        assert result["salary_period"] == "year"

    def test_hourly_salary_detected(self):
        data = {
            "@type": "JobPosting",
            "description": "Role.",
            "baseSalary": {
                "value": {"minValue": 40, "maxValue": 60},
                "unitText": "HOUR",
            },
        }
        html = self._make_jsonld_html(data)
        result = DetailPageExtractor.extract(html)
        assert result["salary_period"] == "hour"

    def test_extracts_posted_at(self):
        data = {
            "@type": "JobPosting",
            "description": "Details here.",
            "datePosted": "2026-03-01",
        }
        html = self._make_jsonld_html(data)
        result = DetailPageExtractor.extract(html)
        assert result["posted_at"] == "2026-03-01"

    def test_extracts_qualifications_string(self):
        data = {
            "@type": "JobPosting",
            "description": "Details.",
            "qualifications": "5 years of experience",
        }
        html = self._make_jsonld_html(data)
        result = DetailPageExtractor.extract(html)
        assert result["requirements"] == ["5 years of experience"]

    def test_non_job_posting_type_ignored(self):
        data = {"@type": "Organization", "name": "Acme"}
        html = self._make_jsonld_html(data)
        result = DetailPageExtractor.extract(html)
        assert "description_raw" not in result or not result.get("description_raw")

    def test_malformed_json_ld_does_not_raise(self):
        html = '<script type="application/ld+json">{bad json}</script><p>Job</p>'
        result = DetailPageExtractor.extract(html)
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Heuristic extraction path
# ---------------------------------------------------------------------------


class TestHeuristicExtraction:
    def test_extracts_description_from_job_description_class(self):
        html = """
        <html><body>
          <div class="job-description">Build great software for our customers.</div>
        </body></html>
        """
        result = DetailPageExtractor.extract(html)
        assert "Build great software" in result.get("description_raw", "")

    def test_extracts_salary_range_k_notation(self):
        html = "<html><body><p>Salary: $120k-$150k per year</p></body></html>"
        result = DetailPageExtractor.extract(html)
        assert result.get("salary_min") == 120_000
        assert result.get("salary_max") == 150_000

    def test_extracts_hourly_salary(self):
        html = "<html><body><p>Rate: $45/hr - $55/hr</p></body></html>"
        result = DetailPageExtractor.extract(html)
        assert result.get("salary_period") == "hour"

    def test_extracts_requirements_from_heading(self):
        html = """
        <html><body>
          <h3>Requirements</h3>
          <ul>
            <li>Python 5+ years</li>
            <li>FastAPI experience</li>
          </ul>
        </body></html>
        """
        result = DetailPageExtractor.extract(html)
        assert "Python 5+ years" in result.get("requirements", [])

    def test_extracts_benefits_from_heading(self):
        html = """
        <html><body>
          <h3>Benefits</h3>
          <ul>
            <li>Health insurance</li>
            <li>401k matching</li>
          </ul>
        </body></html>
        """
        result = DetailPageExtractor.extract(html)
        assert "Health insurance" in result.get("benefits", [])

    def test_missing_fields_return_empty_dict_not_exception(self):
        html = "<html><body><p>Just plain text, no structure.</p></body></html>"
        result = DetailPageExtractor.extract(html)
        assert isinstance(result, dict)
        # description_raw absent or None is fine — no exception

    def test_empty_html_does_not_raise(self):
        result = DetailPageExtractor.extract("")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# _parse_salary_value
# ---------------------------------------------------------------------------


class TestParseSalaryValue:
    def test_integer_string(self):
        assert DetailPageExtractor._parse_salary_value("120000") == 120000.0

    def test_string_with_commas(self):
        assert DetailPageExtractor._parse_salary_value("120,000") == 120000.0

    def test_invalid_returns_none(self):
        assert DetailPageExtractor._parse_salary_value("n/a") is None
