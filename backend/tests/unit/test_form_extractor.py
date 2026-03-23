"""Tests for FormExtractor with mock Playwright objects."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.auto_apply.form_extractor import FormExtractor, FormField

# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _make_locator(
    *,
    attrs: dict[str, str | None] | None = None,
    visible: bool = True,
    input_value: str = "",
    inner_text: str = "",
    tag: str = "input",
    is_checked: bool = False,
    children: list | None = None,
) -> AsyncMock:
    """Create a mock Playwright Locator with typical attributes."""
    attrs = attrs or {}
    loc = AsyncMock()
    loc.get_attribute = AsyncMock(side_effect=lambda name: attrs.get(name))
    loc.is_visible = AsyncMock(return_value=visible)
    loc.input_value = AsyncMock(return_value=input_value)
    loc.inner_text = AsyncMock(return_value=inner_text)
    loc.is_checked = AsyncMock(return_value=is_checked)
    loc.evaluate = AsyncMock(
        side_effect=lambda js: _eval_js(js, tag, attrs)
    )
    loc.page = MagicMock()

    # For locator("option") or locator("role=option")
    child_loc = AsyncMock()
    child_loc.all = AsyncMock(return_value=children or [])
    loc.locator = MagicMock(return_value=child_loc)

    return loc


def _eval_js(js: str, tag: str, attrs: dict[str, str | None]) -> str:
    """Simulate common JS evaluations."""
    if "tagName.toLowerCase" in js and "className" not in js:
        return tag
    if "tagName" in js and "className" in js:
        cls = attrs.get("class", "")
        if cls:
            return f"{tag}.{'.'.join(cls.split())}"
        return tag
    if "closest" in js and "label" in js:
        return attrs.get("_parent_label", "")
    if "closest" in js and "legend" in js:
        return attrs.get("_legend", "")
    return ""


def _make_page(
    *,
    textboxes: list[AsyncMock] | None = None,
    email_inputs: list[AsyncMock] | None = None,
    tel_inputs: list[AsyncMock] | None = None,
    url_inputs: list[AsyncMock] | None = None,
    number_inputs: list[AsyncMock] | None = None,
    textareas: list[AsyncMock] | None = None,
    comboboxes: list[AsyncMock] | None = None,
    listboxes: list[AsyncMock] | None = None,
    selects: list[AsyncMock] | None = None,
    checkboxes: list[AsyncMock] | None = None,
    radios: list[AsyncMock] | None = None,
    file_inputs: list[AsyncMock] | None = None,
    spinbuttons: list[AsyncMock] | None = None,
    iframes: list[AsyncMock] | None = None,
    label_elements: dict[str, AsyncMock] | None = None,
) -> AsyncMock:
    """Create a mock Playwright Page with form elements."""
    page = AsyncMock()
    label_elements = label_elements or {}

    selector_map: dict[str, list[AsyncMock]] = {
        "role=textbox": textboxes or [],
        'input[type="email"]': email_inputs or [],
        'input[type="tel"]': tel_inputs or [],
        'input[type="url"]': url_inputs or [],
        'input[type="number"]': number_inputs or [],
        "textarea": textareas or [],
        "role=combobox": comboboxes or [],
        "role=listbox": listboxes or [],
        "select": selects or [],
        "role=checkbox": checkboxes or [],
        "role=radio": radios or [],
        'input[type="file"]': file_inputs or [],
        "role=spinbutton": spinbuttons or [],
        "iframe": iframes or [],
    }

    def make_loc_group(selector: str) -> MagicMock:
        group = MagicMock()
        items = selector_map.get(selector, [])
        group.all = AsyncMock(return_value=items)
        group.count = AsyncMock(return_value=len(items))
        if items:
            group.first = items[0]
        return group

    page.locator = MagicMock(side_effect=make_loc_group)

    # For label lookup: page.locator('label[for="xyz"]')
    def label_side_effect(sel: str) -> MagicMock:
        # Check if it's a label lookup
        for key_sel, mock_label in label_elements.items():
            if key_sel in sel:
                group = MagicMock()
                group.count = AsyncMock(return_value=1)
                group.first = mock_label
                return group
        # Also try selector_map
        for map_sel, items in selector_map.items():
            if sel == map_sel:
                group = MagicMock()
                group.all = AsyncMock(return_value=items)
                group.count = AsyncMock(return_value=len(items))
                if items:
                    group.first = items[0]
                return group
        # Default empty
        group = MagicMock()
        group.all = AsyncMock(return_value=[])
        group.count = AsyncMock(return_value=0)
        return group

    page.locator = MagicMock(side_effect=label_side_effect)

    return page


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFormExtractorTextInputs:
    """Test extraction of text-like inputs."""

    @pytest.mark.asyncio
    async def test_extracts_text_input_with_aria_label(self) -> None:
        loc = _make_locator(attrs={"aria-label": "First Name", "id": "fname", "type": "text"})
        page = _make_page(textboxes=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert len(fields) == 1
        f = fields[0]
        assert f.label == "First Name"
        assert f.field_type == "text"
        assert f.locator_desc == "#fname"

    @pytest.mark.asyncio
    async def test_extracts_text_input_with_label_for(self) -> None:
        label_mock = AsyncMock()
        label_mock.inner_text = AsyncMock(return_value="Last Name")

        loc = _make_locator(attrs={"id": "lname", "type": "text"})
        page = _make_page(
            textboxes=[loc],
            label_elements={'label[for="lname"]': label_mock},
        )

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert len(fields) == 1
        assert fields[0].label == "Last Name"

    @pytest.mark.asyncio
    async def test_extracts_text_input_with_placeholder(self) -> None:
        loc = _make_locator(attrs={"placeholder": "Enter your email", "name": "email_field"})
        page = _make_page(textboxes=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert len(fields) == 1
        assert fields[0].label == "Enter your email"
        assert fields[0].name_attr == "email_field"

    @pytest.mark.asyncio
    async def test_hidden_inputs_are_skipped(self) -> None:
        loc = _make_locator(attrs={"id": "hidden1"}, visible=False)
        page = _make_page(textboxes=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert len(fields) == 0

    @pytest.mark.asyncio
    async def test_extracts_email_input_type(self) -> None:
        loc = _make_locator(attrs={"type": "email", "id": "user_email", "aria-label": "Email"})
        page = _make_page(email_inputs=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert len(fields) == 1
        assert fields[0].field_type == "email"
        assert fields[0].label == "Email"

    @pytest.mark.asyncio
    async def test_extracts_phone_input(self) -> None:
        loc = _make_locator(attrs={"type": "tel", "name": "phone", "aria-label": "Phone Number"})
        page = _make_page(tel_inputs=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert len(fields) == 1
        assert fields[0].field_type == "phone"

    @pytest.mark.asyncio
    async def test_deduplicates_by_selector(self) -> None:
        """Same element found by both role=textbox and input[type=email] should appear once."""
        loc = _make_locator(attrs={"id": "email1", "aria-label": "Email", "type": "email"})
        page = _make_page(textboxes=[loc], email_inputs=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        # Should deduplicate based on selector (#email1)
        assert len(fields) == 1


class TestFormExtractorTextareas:
    @pytest.mark.asyncio
    async def test_extracts_textarea(self) -> None:
        loc = _make_locator(
            attrs={"id": "cover", "aria-label": "Cover Letter"},
            tag="textarea",
        )
        page = _make_page(textareas=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert len(fields) == 1
        assert fields[0].field_type == "textarea"
        assert fields[0].label == "Cover Letter"


class TestFormExtractorSelects:
    @pytest.mark.asyncio
    async def test_extracts_combobox_with_options(self) -> None:
        opt1 = AsyncMock()
        opt1.inner_text = AsyncMock(return_value="United States")
        opt2 = AsyncMock()
        opt2.inner_text = AsyncMock(return_value="Canada")

        loc = _make_locator(
            attrs={"id": "country", "aria-label": "Country", "role": "combobox"},
        )
        # Set up option children
        option_group = AsyncMock()
        option_group.all = AsyncMock(return_value=[opt1, opt2])
        role_option_group = AsyncMock()
        role_option_group.all = AsyncMock(return_value=[])
        loc.locator = MagicMock(
            side_effect=lambda sel: option_group if sel == "option" else role_option_group,
        )

        page = _make_page(comboboxes=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert len(fields) == 1
        assert fields[0].field_type == "select"
        assert fields[0].options == ["United States", "Canada"]

    @pytest.mark.asyncio
    async def test_extracts_native_select(self) -> None:
        opt1 = AsyncMock()
        opt1.inner_text = AsyncMock(return_value="Yes")
        opt2 = AsyncMock()
        opt2.inner_text = AsyncMock(return_value="No")

        loc = _make_locator(
            attrs={"name": "relocate", "aria-label": "Willing to Relocate"},
            tag="select",
        )
        option_group = AsyncMock()
        option_group.all = AsyncMock(return_value=[opt1, opt2])
        role_option_group = AsyncMock()
        role_option_group.all = AsyncMock(return_value=[])
        loc.locator = MagicMock(
            side_effect=lambda sel: option_group if sel == "option" else role_option_group,
        )

        page = _make_page(selects=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert len(fields) == 1
        assert fields[0].field_type == "select"
        assert fields[0].options == ["Yes", "No"]


class TestFormExtractorCheckboxes:
    @pytest.mark.asyncio
    async def test_extracts_checkbox(self) -> None:
        loc = _make_locator(
            attrs={"id": "agree", "aria-label": "I agree to terms", "role": "checkbox"},
            is_checked=True,
        )
        page = _make_page(checkboxes=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert len(fields) == 1
        assert fields[0].field_type == "checkbox"
        assert fields[0].label == "I agree to terms"
        assert fields[0].current_value == "true"


class TestFormExtractorRadioGroups:
    @pytest.mark.asyncio
    async def test_extracts_radio_group(self) -> None:
        r1 = _make_locator(attrs={
            "name": "auth", "value": "yes", "aria-label": "Yes",
            "role": "radio", "_legend": "Work Authorization",
        })
        r2 = _make_locator(attrs={
            "name": "auth", "value": "no", "aria-label": "No",
            "role": "radio", "_legend": "Work Authorization",
        })
        page = _make_page(radios=[r1, r2])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert len(fields) == 1
        assert fields[0].field_type == "radio"
        assert fields[0].name_attr == "auth"
        assert "Yes" in fields[0].options
        assert "No" in fields[0].options


class TestFormExtractorFileUploads:
    @pytest.mark.asyncio
    async def test_extracts_file_upload(self) -> None:
        loc = _make_locator(
            attrs={"name": "resume", "aria-label": "Upload Resume", "type": "file"},
        )
        page = _make_page(file_inputs=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert len(fields) == 1
        assert fields[0].field_type == "file"
        assert fields[0].label == "Upload Resume"


class TestFormExtractorRequired:
    @pytest.mark.asyncio
    async def test_detects_required_attribute(self) -> None:
        loc = _make_locator(attrs={"id": "email", "aria-label": "Email", "required": ""})
        page = _make_page(textboxes=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert fields[0].required is True

    @pytest.mark.asyncio
    async def test_detects_aria_required(self) -> None:
        loc = _make_locator(attrs={"id": "phone", "aria-label": "Phone", "aria-required": "true"})
        page = _make_page(textboxes=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert fields[0].required is True

    @pytest.mark.asyncio
    async def test_not_required_when_absent(self) -> None:
        loc = _make_locator(attrs={"id": "website", "aria-label": "Website"})
        page = _make_page(textboxes=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert fields[0].required is False


class TestFormExtractorLabelInference:
    @pytest.mark.asyncio
    async def test_label_from_aria_labelledby(self) -> None:
        label_el = AsyncMock()
        label_el.inner_text = AsyncMock(return_value="Your Name")

        loc = _make_locator(attrs={"id": "name1", "aria-labelledby": "name_label"})

        # Mock the page for aria-labelledby lookup
        page = _make_page(
            textboxes=[loc],
            label_elements={"#name_label": label_el},
        )

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert len(fields) == 1
        assert fields[0].label == "Your Name"

    @pytest.mark.asyncio
    async def test_label_fallback_to_name_attr(self) -> None:
        loc = _make_locator(attrs={"name": "applicant_city"})
        page = _make_page(textboxes=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert fields[0].label == "applicant city"

    @pytest.mark.asyncio
    async def test_label_fallback_to_parent_label(self) -> None:
        loc = _make_locator(attrs={"id": "f1", "_parent_label": "Company Name"})

        page = _make_page(textboxes=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert fields[0].label == "Company Name"


class TestFormExtractorSelector:
    @pytest.mark.asyncio
    async def test_selector_prefers_id(self) -> None:
        loc = _make_locator(attrs={"id": "myfield", "name": "field1"})
        page = _make_page(textboxes=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert fields[0].locator_desc == "#myfield"

    @pytest.mark.asyncio
    async def test_selector_falls_back_to_name(self) -> None:
        loc = _make_locator(attrs={"name": "field1"})
        page = _make_page(textboxes=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert fields[0].locator_desc == '[name="field1"]'

    @pytest.mark.asyncio
    async def test_selector_uses_data_automation_id(self) -> None:
        loc = _make_locator(attrs={"data-automation-id": "firstName"})
        page = _make_page(textboxes=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert fields[0].locator_desc == '[data-automation-id="firstName"]'

    @pytest.mark.asyncio
    async def test_selector_uses_data_testid(self) -> None:
        loc = _make_locator(attrs={"data-testid": "input-email"})
        page = _make_page(textboxes=[loc])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert fields[0].locator_desc == '[data-testid="input-email"]'


class TestFormExtractorIframes:
    @pytest.mark.asyncio
    async def test_extract_fields_checks_iframes(self) -> None:
        """Full extract_fields call should try iframes."""
        textbox = _make_locator(attrs={"id": "name", "aria-label": "Name"})
        page = _make_page(textboxes=[textbox])

        extractor = FormExtractor()
        fields = await extractor.extract_fields(page)

        # Should at least get the main page field
        assert len(fields) >= 1
        assert fields[0].label == "Name"

    @pytest.mark.asyncio
    async def test_iframe_pattern_detection(self) -> None:
        extractor = FormExtractor()
        assert "icims" in extractor.IFRAME_PATTERNS
        assert "myworkdayjobs" in extractor.IFRAME_PATTERNS


class TestFormExtractorMixedForm:
    """Test with a realistic mix of field types."""

    @pytest.mark.asyncio
    async def test_mixed_form_extraction(self) -> None:
        first_name = _make_locator(attrs={
            "id": "first_name", "aria-label": "First Name", "required": "",
        })
        last_name = _make_locator(attrs={
            "id": "last_name", "aria-label": "Last Name", "required": "",
        })
        email = _make_locator(attrs={
            "id": "email", "aria-label": "Email Address", "type": "email", "required": "",
        })
        phone = _make_locator(attrs={
            "name": "phone", "aria-label": "Phone Number", "type": "tel",
        })
        resume = _make_locator(attrs={
            "name": "resume", "aria-label": "Upload Resume", "type": "file",
        })
        agree = _make_locator(attrs={
            "id": "terms", "aria-label": "I agree to the terms",
            "role": "checkbox", "required": "",
        })

        page = _make_page(
            textboxes=[first_name, last_name],
            email_inputs=[email],
            tel_inputs=[phone],
            file_inputs=[resume],
            checkboxes=[agree],
        )

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        # Should get all 6 fields
        assert len(fields) == 6
        types = {f.field_type for f in fields}
        assert types == {"text", "email", "phone", "file", "checkbox"}
        required_fields = [f for f in fields if f.required]
        assert len(required_fields) == 4  # first, last, email, terms


class TestFormFieldDataclass:
    def test_formfield_defaults(self) -> None:
        f = FormField(
            label="Test",
            field_type="text",
            required=False,
            aria_role="textbox",
            locator_desc="#test",
        )
        assert f.options == []
        assert f.current_value is None
        assert f.placeholder is None
        assert f.name_attr is None

    def test_formfield_with_options(self) -> None:
        f = FormField(
            label="Country",
            field_type="select",
            required=True,
            aria_role="combobox",
            locator_desc="#country",
            options=["US", "CA", "UK"],
        )
        assert len(f.options) == 3
