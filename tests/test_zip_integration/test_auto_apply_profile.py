"""Test application profile management."""
import pytest
from backend.auto_apply.profile import ApplicationProfile, validate_profile


class TestApplicationProfile:
    def test_create_full(self):
        p = ApplicationProfile(
            name="John Doe",
            email="john@example.com",
            phone="+1-555-0123",
            linkedin="https://linkedin.com/in/johndoe",
            github="https://github.com/johndoe",
            portfolio="https://johndoe.dev",
            location="San Francisco, CA",
            work_authorization="US Citizen",
            years_experience=5,
            education_summary="BS CS, MIT",
            current_title="Senior Engineer",
            desired_salary="$150,000-$200,000",
        )
        assert p.name == "John Doe"
        assert p.years_experience == 5

    def test_create_minimal(self):
        p = ApplicationProfile(name="Jane", email="jane@test.com")
        assert p.name == "Jane"
        assert p.phone is None
        assert p.linkedin is None
        assert p.years_experience is None

    def test_to_dict(self):
        p = ApplicationProfile(name="John", email="j@test.com", phone="+1-555-0123")
        d = p.to_dict()
        assert isinstance(d, dict)
        assert d["name"] == "John"
        assert d["email"] == "j@test.com"
        assert d["phone"] == "+1-555-0123"

    def test_from_dict(self):
        d = {"name": "John", "email": "j@test.com", "years_experience": 5}
        p = ApplicationProfile.from_dict(d)
        assert p.name == "John"
        assert p.years_experience == 5

    def test_from_dict_ignores_unknown(self):
        d = {"name": "John", "email": "j@test.com", "unknown_field": "value"}
        p = ApplicationProfile.from_dict(d)
        assert p.name == "John"

    def test_from_dict_empty(self):
        p = ApplicationProfile.from_dict({})
        assert p.name is None
        assert p.email is None


class TestValidateProfile:
    def test_valid_full_profile(self):
        p = ApplicationProfile(name="John", email="john@test.com")
        errors = validate_profile(p)
        assert len(errors) == 0

    def test_missing_name(self):
        p = ApplicationProfile(name=None, email="john@test.com")
        errors = validate_profile(p)
        assert any("name" in e.lower() for e in errors)

    def test_missing_email(self):
        p = ApplicationProfile(name="John", email=None)
        errors = validate_profile(p)
        assert any("email" in e.lower() for e in errors)

    def test_invalid_email(self):
        p = ApplicationProfile(name="John", email="not-an-email")
        errors = validate_profile(p)
        assert any("email" in e.lower() for e in errors)

    def test_valid_email(self):
        p = ApplicationProfile(name="John", email="valid@example.com")
        errors = validate_profile(p)
        assert len(errors) == 0
