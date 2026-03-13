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
        assert fuzzy_match_label("First Name", ["full_name", "email"]) == "full_name"

    def test_close_match(self):
        result = fuzzy_match_label("Your Email Address", ["email", "full_name", "phone"])
        assert result == "email"

    def test_no_match(self):
        result = fuzzy_match_label("Random Label XYZ", ["email", "full_name"])
        assert result is None

    def test_case_insensitive(self):
        result = fuzzy_match_label("EMAIL ADDRESS", ["email", "full_name"])
        assert result == "email"

    def test_linkedin_url_match(self):
        result = fuzzy_match_label("LinkedIn Profile URL", ["linkedin_url", "github_url", "email"])
        assert result == "linkedin_url"

    def test_github_url_match(self):
        result = fuzzy_match_label("GitHub URL", ["github_url", "linkedin_url", "email"])
        assert result == "github_url"


class TestDetectFieldType:
    def test_email_field(self):
        assert detect_field_type("email", "email-input", "") == "email"

    def test_phone_field(self):
        assert detect_field_type("phone", "phone-input", "tel") == "phone"

    def test_name_field(self):
        assert detect_field_type("name", "name-field", "text") == "full_name"

    def test_file_field(self):
        assert detect_field_type("resume", "upload", "file") == "file"

    def test_url_input_type(self):
        assert detect_field_type("website", "website-field", "url") == "portfolio_url"

    def test_unknown_field(self):
        result = detect_field_type("random", "random-id", "text")
        assert result == "text"


class TestFieldMapping:
    def test_create_minimal(self):
        fm = FieldMapping(
            label="First Name",
            field_type="full_name",
            profile_key="full_name",
            selector="#first-name",
        )
        assert fm.label == "First Name"
        assert fm.profile_key == "full_name"
        assert fm.required is False
        assert fm.field_id == ""
        assert fm.confidence == 0.0

    def test_create_with_all_fields(self):
        fm = FieldMapping(
            label="Email",
            field_type="email",
            profile_key="email",
            selector="#email",
            required=True,
            field_id="email-input-1",
            confidence=0.95,
        )
        assert fm.required is True
        assert fm.field_id == "email-input-1"
        assert fm.confidence == 0.95

    def test_field_id_default_empty_string(self):
        fm = FieldMapping(label="X", field_type="email", profile_key="email", selector="#x")
        assert fm.field_id == ""

    def test_confidence_default_zero(self):
        fm = FieldMapping(label="X", field_type="email", profile_key="email", selector="#x")
        assert fm.confidence == 0.0


@pytest.mark.asyncio
class TestGenericATSFiller:
    async def test_fill_greenhouse_form(self):
        profile = ApplicationProfile(full_name="John Doe", email="john@test.com", phone="+1-555-0123")

        mock_page = AsyncMock()
        mock_field1 = AsyncMock()
        mock_field1.get_attribute = AsyncMock(
            side_effect=lambda attr: {"type": "text", "name": "full_name", "id": "full_name"}.get(attr)
        )
        mock_field1.text_content = AsyncMock(return_value="")

        mock_label1 = AsyncMock()
        mock_label1.text_content = AsyncMock(return_value="Full Name")
        mock_label1.get_attribute = AsyncMock(return_value="full_name")

        mock_page.query_selector_all = AsyncMock(return_value=[mock_label1])
        mock_page.query_selector = AsyncMock(return_value=mock_field1)

        filler = GenericATSFiller(profile)
        result = await filler.analyze_form(mock_page)
        assert isinstance(result, dict)

    async def test_filler_creates_result(self):
        profile = ApplicationProfile(full_name="John Doe", email="john@test.com")
        filler = GenericATSFiller(profile)
        assert filler.profile.full_name == "John Doe"

    async def test_profile_keys_include_new_names(self):
        profile = ApplicationProfile(full_name="Jane", email="jane@test.com")
        filler = GenericATSFiller(profile)
        assert "full_name" in filler._profile_keys
        assert "linkedin_url" in filler._profile_keys
        assert "github_url" in filler._profile_keys
        assert "portfolio_url" in filler._profile_keys
        # Old names must NOT be present
        assert "name" not in filler._profile_keys
        assert "linkedin" not in filler._profile_keys
        assert "github" not in filler._profile_keys
        assert "portfolio" not in filler._profile_keys
