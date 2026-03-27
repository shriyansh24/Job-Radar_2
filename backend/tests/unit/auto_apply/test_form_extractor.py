from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.auto_apply.form_extractor import FormExtractor, FormField


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
    attrs = attrs or {}
    locator = AsyncMock()
    locator.get_attribute = AsyncMock(side_effect=lambda name: attrs.get(name))
    locator.is_visible = AsyncMock(return_value=visible)
    locator.input_value = AsyncMock(return_value=input_value)
    locator.inner_text = AsyncMock(return_value=inner_text)
    locator.is_checked = AsyncMock(return_value=is_checked)
    locator.evaluate = AsyncMock(side_effect=lambda js: _eval_js(js, tag, attrs))
    locator.page = MagicMock()

    child_group = AsyncMock()
    child_group.all = AsyncMock(return_value=children or [])
    locator.locator = MagicMock(return_value=child_group)
    return locator


def _eval_js(js: str, tag: str, attrs: dict[str, str | None]) -> str:
    if "tagName.toLowerCase" in js and "className" not in js:
        return tag
    if "tagName" in js and "className" in js:
        css_class = attrs.get("class", "")
        return f"{tag}.{'.'.join(css_class.split())}" if css_class else tag
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

    def locator_side_effect(selector: str) -> MagicMock:
        for key_selector, mock_label in label_elements.items():
            if key_selector in selector:
                group = MagicMock()
                group.count = AsyncMock(return_value=1)
                group.first = mock_label
                return group

        group = MagicMock()
        items = selector_map.get(selector, [])
        group.all = AsyncMock(return_value=items)
        group.count = AsyncMock(return_value=len(items))
        if items:
            group.first = items[0]
        return group

    page.locator = MagicMock(side_effect=locator_side_effect)
    return page


class TestFormExtractorTextInputs:
    @pytest.mark.asyncio
    async def test_extracts_text_input_with_aria_label(self) -> None:
        locator = _make_locator(
            attrs={"aria-label": "First Name", "id": "fname", "type": "text"}
        )
        page = _make_page(textboxes=[locator])

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert len(fields) == 1
        field = fields[0]
        assert field.label == "First Name"
        assert field.field_type == "text"
        assert field.locator_desc == "#fname"

    @pytest.mark.asyncio
    async def test_extracts_text_input_with_label_for(self) -> None:
        label = AsyncMock()
        label.inner_text = AsyncMock(return_value="Last Name")

        locator = _make_locator(attrs={"id": "lname", "type": "text"})
        page = _make_page(textboxes=[locator], label_elements={'label[for="lname"]': label})

        extractor = FormExtractor()
        fields = await extractor._extract_from_context(page)

        assert len(fields) == 1
        assert fields[0].label == "Last Name"

    @pytest.mark.asyncio
    async def test_hidden_inputs_are_skipped(self) -> None:
        page = _make_page(textboxes=[_make_locator(attrs={"id": "hidden"}, visible=False)])
        fields = await FormExtractor()._extract_from_context(page)
        assert fields == []

    @pytest.mark.asyncio
    async def test_deduplicates_by_selector(self) -> None:
        locator = _make_locator(attrs={"id": "email1", "aria-label": "Email", "type": "email"})
        page = _make_page(textboxes=[locator], email_inputs=[locator])
        fields = await FormExtractor()._extract_from_context(page)
        assert len(fields) == 1


class TestFormExtractorOtherFieldTypes:
    @pytest.mark.asyncio
    async def test_extracts_textarea(self) -> None:
        locator = _make_locator(
            attrs={"id": "cover", "aria-label": "Cover Letter"},
            tag="textarea",
        )
        fields = await FormExtractor()._extract_from_context(_make_page(textareas=[locator]))
        assert len(fields) == 1
        assert fields[0].field_type == "textarea"

    @pytest.mark.asyncio
    async def test_extracts_select_with_options(self) -> None:
        opt1 = AsyncMock()
        opt1.inner_text = AsyncMock(return_value="United States")
        opt2 = AsyncMock()
        opt2.inner_text = AsyncMock(return_value="Canada")
        locator = _make_locator(
            attrs={"id": "country", "aria-label": "Country", "role": "combobox"}
        )
        option_group = AsyncMock()
        option_group.all = AsyncMock(return_value=[opt1, opt2])
        empty_group = AsyncMock()
        empty_group.all = AsyncMock(return_value=[])
        locator.locator = MagicMock(
            side_effect=lambda sel: option_group if sel == "option" else empty_group
        )

        fields = await FormExtractor()._extract_from_context(_make_page(comboboxes=[locator]))
        assert fields[0].field_type == "select"
        assert fields[0].options == ["United States", "Canada"]

    @pytest.mark.asyncio
    async def test_extracts_checkbox(self) -> None:
        locator = _make_locator(
            attrs={"id": "agree", "aria-label": "I agree", "role": "checkbox"},
            is_checked=True,
        )
        fields = await FormExtractor()._extract_from_context(_make_page(checkboxes=[locator]))
        assert fields[0].field_type == "checkbox"
        assert fields[0].current_value == "true"

    @pytest.mark.asyncio
    async def test_extracts_radio_group(self) -> None:
        radio1 = _make_locator(
            attrs={
                "name": "auth",
                "value": "yes",
                "aria-label": "Yes",
                "role": "radio",
                "_legend": "Work Authorization",
            }
        )
        radio2 = _make_locator(
            attrs={
                "name": "auth",
                "value": "no",
                "aria-label": "No",
                "role": "radio",
                "_legend": "Work Authorization",
            }
        )
        fields = await FormExtractor()._extract_from_context(_make_page(radios=[radio1, radio2]))
        assert len(fields) == 1
        assert fields[0].field_type == "radio"
        assert "Yes" in fields[0].options

    @pytest.mark.asyncio
    async def test_extract_fields_checks_iframes(self) -> None:
        page = _make_page(textboxes=[_make_locator(attrs={"id": "name", "aria-label": "Name"})])
        fields = await FormExtractor().extract_fields(page)
        assert fields[0].label == "Name"


class TestFormFieldDataclass:
    def test_defaults(self) -> None:
        field = FormField(
            label="Test",
            field_type="text",
            required=False,
            aria_role="textbox",
            locator_desc="#test",
        )
        assert field.options == []
        assert field.current_value is None
