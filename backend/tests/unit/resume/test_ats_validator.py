from __future__ import annotations

from app.resume.validator import ATSValidator


def _make_full_ir() -> dict:
    return {
        "contact": {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "555-123-4567",
        },
        "summary": "Experienced software engineer with 5 years of Python backend expertise.",
        "work": [
            {
                "company": "Acme Corp",
                "title": "Senior Engineer",
                "start_date": "Jan 2020",
                "end_date": "Present",
                "bullets": [
                    "Led team of 5 engineers building microservices",
                    "Reduced deploy time by 40% through CI/CD improvements",
                    "Implemented automated testing achieving 90% coverage",
                    "Managed $500K annual infrastructure budget",
                ],
            }
        ],
        "education": [
            {
                "institution": "MIT",
                "degree": "BS",
                "field": "Computer Science",
                "end_date": "2019",
            }
        ],
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
    }


def _make_minimal_ir() -> dict:
    return {
        "contact": {"name": "Unknown"},
    }


class TestATSValidator:
    def test_full_resume_scores_high(self):
        validator = ATSValidator()
        result = validator.validate(_make_full_ir())
        assert result.score >= 70
        assert result.passed is True
        assert len(result.checks) > 0
        assert len(result.warnings) < len(result.checks)

    def test_minimal_resume_scores_low(self):
        validator = ATSValidator()
        result = validator.validate(_make_minimal_ir())
        assert result.score < 60
        assert result.passed is False
        assert len(result.warnings) > 0

    def test_check_names_are_present(self):
        validator = ATSValidator()
        result = validator.validate(_make_full_ir())
        check_fields = {check.field for check in result.checks}
        expected_fields = {
            "contact_name",
            "contact_email",
            "contact_phone",
            "has_work",
            "has_education",
            "has_skills",
            "has_summary",
            "bullet_quality",
            "no_image_only",
            "text_length",
            "standard_headers",
        }
        assert expected_fields == check_fields

    def test_missing_email_flagged(self):
        ir = _make_full_ir()
        ir["contact"]["email"] = ""
        validator = ATSValidator()
        result = validator.validate(ir)
        email_check = next(
            check for check in result.checks if check.field == "contact_email"
        )
        assert email_check.passed is False

    def test_missing_phone_flagged(self):
        ir = _make_full_ir()
        ir["contact"]["phone"] = ""
        validator = ATSValidator()
        result = validator.validate(ir)
        phone_check = next(
            check for check in result.checks if check.field == "contact_phone"
        )
        assert phone_check.passed is False

    def test_no_work_section_flagged(self):
        ir = _make_full_ir()
        ir["work"] = []
        validator = ATSValidator()
        result = validator.validate(ir)
        work_check = next(check for check in result.checks if check.field == "has_work")
        assert work_check.passed is False

    def test_no_skills_flagged(self):
        ir = _make_full_ir()
        ir["skills"] = []
        validator = ATSValidator()
        result = validator.validate(ir)
        skills_check = next(
            check for check in result.checks if check.field == "has_skills"
        )
        assert skills_check.passed is False

    def test_skill_categories_count_as_skills(self):
        ir = _make_full_ir()
        ir["skills"] = []
        ir["skill_categories"] = {"Languages": ["Python", "Go"]}
        validator = ATSValidator()
        result = validator.validate(ir)
        skills_check = next(
            check for check in result.checks if check.field == "has_skills"
        )
        assert skills_check.passed is True

    def test_no_summary_flagged(self):
        ir = _make_full_ir()
        ir["summary"] = ""
        validator = ATSValidator()
        result = validator.validate(ir)
        summary_check = next(
            check for check in result.checks if check.field == "has_summary"
        )
        assert summary_check.passed is False

    def test_bullet_quality_with_good_bullets(self):
        validator = ATSValidator()
        result = validator.validate(_make_full_ir())
        quality_check = next(
            check for check in result.checks if check.field == "bullet_quality"
        )
        assert quality_check.passed is True
        assert quality_check.details is not None
        assert quality_check.details["action_verb_ratio"] >= 0.5

    def test_bullet_quality_with_weak_bullets(self):
        ir = _make_full_ir()
        ir["work"][0]["bullets"] = [
            "Was responsible for things",
            "Helped with stuff",
            "Worked on projects",
            "Did various tasks",
        ]
        validator = ATSValidator()
        result = validator.validate(ir)
        quality_check = next(
            check for check in result.checks if check.field == "bullet_quality"
        )
        assert quality_check.passed is False

    def test_text_length_check(self):
        validator = ATSValidator()
        result = validator.validate(_make_full_ir())
        length_check = next(
            check for check in result.checks if check.field == "text_length"
        )
        assert length_check.passed is True
        assert length_check.details is not None
        assert length_check.details["length"] > 0

    def test_standard_headers_all_present(self):
        validator = ATSValidator()
        result = validator.validate(_make_full_ir())
        headers_check = next(
            check for check in result.checks if check.field == "standard_headers"
        )
        assert headers_check.passed is True

    def test_standard_headers_missing_education(self):
        ir = _make_full_ir()
        ir["education"] = []
        validator = ATSValidator()
        result = validator.validate(ir)
        headers_check = next(
            check for check in result.checks if check.field == "standard_headers"
        )
        assert headers_check.passed is False
        assert "education" in headers_check.details["missing"]

    def test_extracted_text_length_reported(self):
        validator = ATSValidator()
        result = validator.validate(_make_full_ir())
        assert result.extracted_text_length > 0

    def test_score_is_bounded(self):
        validator = ATSValidator()
        result = validator.validate(_make_full_ir())
        assert 0 <= result.score <= 100
        result2 = validator.validate(_make_minimal_ir())
        assert 0 <= result2.score <= 100

    def test_empty_ir(self):
        validator = ATSValidator()
        result = validator.validate({})
        assert result.score < 30
        assert result.passed is False

    def test_warnings_match_failed_checks(self):
        validator = ATSValidator()
        result = validator.validate(_make_full_ir())
        failed_count = sum(1 for check in result.checks if not check.passed)
        assert len(result.warnings) == failed_count
