"""Test generic ATS form filler with mocked Playwright."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.auto_apply.ats_filler import (
    GenericATSFiller,
    fuzzy_match_label,
    detect_field_type,
    FieldMapping,
)
from backend.auto_apply.profile import ApplicationProfile


class TestFuzzyMatchLabel:
    def test_exact_match(self):
        assert fuzzy_match_label("First Name", ["first_name", "name", "email"]) == "first_name"

    def test_close_match(self):
        result = fuzzy_match_label("Your Email Address", ["email", "name", "phone"])
        assert result == "email"

    def test_no_match(self):
        result = fuzzy_match_label("Random Label XYZ", ["email", "name"])
        assert result is None

    def test_case_insensitive(self):
        result = fuzzy_match_label("EMAIL ADDRESS", ["email", "name"])
        assert result == "email"


class TestDetectFieldType:
    def test_email_field(self):
        assert detect_field_type("email", "email-input", "") == "email"

    def test_phone_field(self):
        assert detect_field_type("phone", "phone-input", "tel") == "phone"

    def test_name_field(self):
        assert detect_field_type("name", "name-field", "text") == "name"

    def test_file_field(self):
        assert detect_field_type("resume", "upload", "file") == "file"

    def test_unknown_field(self):
        result = detect_field_type("random", "random-id", "text")
        assert result == "text"


class TestFieldMapping:
    def test_create(self):
        fm = FieldMapping(label="First Name", field_type="name", profile_key="name", selector="#first-name")
        assert fm.label == "First Name"
        assert fm.profile_key == "name"


@pytest.mark.asyncio
class TestGenericATSFiller:
    async def test_fill_greenhouse_form(self):
        profile = ApplicationProfile(name="John Doe", email="john@test.com", phone="+1-555-0123")

        mock_page = AsyncMock()
        # Mock finding form fields
        mock_field1 = AsyncMock()
        mock_field1.get_attribute = AsyncMock(side_effect=lambda attr: {"type": "text", "name": "first_name", "id": "first_name"}.get(attr))
        mock_field1.text_content = AsyncMock(return_value="")

        mock_label1 = AsyncMock()
        mock_label1.text_content = AsyncMock(return_value="First Name")
        mock_label1.get_attribute = AsyncMock(return_value="first_name")

        mock_page.query_selector_all = AsyncMock(return_value=[mock_label1])
        mock_page.query_selector = AsyncMock(return_value=mock_field1)

        filler = GenericATSFiller(profile)
        result = await filler.analyze_form(mock_page)
        assert isinstance(result, dict)

    async def test_filler_creates_result(self):
        profile = ApplicationProfile(name="John Doe", email="john@test.com")
        filler = GenericATSFiller(profile)
        assert filler.profile.name == "John Doe"
