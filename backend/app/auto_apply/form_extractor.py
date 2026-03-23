"""Accessibility-based form field extraction using Playwright ARIA locators.

Extracts structured FormField data from any ATS application form using
the accessibility tree (ARIA roles, labels) rather than brittle CSS selectors.
Handles standard HTML forms, iframes (iCIMS), and can be extended for shadow DOM.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import FrameLocator, Locator, Page

logger = logging.getLogger(__name__)


@dataclass
class FormField:
    """A single form field extracted from the page accessibility tree."""

    label: str
    field_type: str  # "text", "email", "phone", "select", "checkbox", "radio", "file", "textarea"
    required: bool
    aria_role: str
    locator_desc: str  # Selector string for re-locating the element
    options: list[str] = field(default_factory=list)
    current_value: str | None = None
    placeholder: str | None = None
    name_attr: str | None = None


class FormExtractor:
    """Extract form fields using Playwright ARIA locators.

    Uses the accessibility tree rather than the deprecated
    ``page.accessibility.snapshot()`` API. Supports standard HTML forms
    and iframe-embedded forms (e.g. iCIMS).
    """

    # ARIA roles that map to extractable form controls
    _TEXTBOX_ROLE = "textbox"
    _COMBOBOX_ROLE = "combobox"
    _LISTBOX_ROLE = "listbox"
    _CHECKBOX_ROLE = "checkbox"
    _RADIO_ROLE = "radio"
    _SPINBUTTON_ROLE = "spinbutton"

    # iframe URL patterns for ATS systems that embed forms
    IFRAME_PATTERNS: list[str] = [
        "icims",
        "myworkdayjobs",
        "lever.co",
        "ashbyhq",
    ]

    async def extract_fields(self, page: Page) -> list[FormField]:
        """Extract all form fields from the page, including iframe content.

        Args:
            page: Playwright Page object with the application form loaded.

        Returns:
            List of FormField dataclasses describing every detected field.
        """
        fields: list[FormField] = []

        # Extract from main page
        fields.extend(await self._extract_from_context(page))

        # Check for iframe-embedded forms
        iframe_fields = await self._extract_from_iframes(page)
        fields.extend(iframe_fields)

        logger.info("Extracted %d form fields (%d from iframes)", len(fields), len(iframe_fields))
        return fields

    async def _extract_from_context(
        self, ctx: Page | FrameLocator, prefix: str = ""
    ) -> list[FormField]:
        """Extract fields from a page or frame context."""
        fields: list[FormField] = []
        seen_selectors: set[str] = set()

        # --- Text inputs (role=textbox) ---
        for locator in await ctx.locator("role=textbox").all():
            if not await self._is_visible_safe(locator):
                continue
            f = await self._extract_input(locator, prefix, ctx=ctx)
            if f.locator_desc not in seen_selectors:
                seen_selectors.add(f.locator_desc)
                fields.append(f)

        # --- Email / phone / url inputs (may share role=textbox but have type attr) ---
        for input_type in ("email", "tel", "url", "number"):
            for locator in await ctx.locator(f'input[type="{input_type}"]').all():
                if not await self._is_visible_safe(locator):
                    continue
                sel = await self._build_selector(locator, prefix)
                if sel not in seen_selectors:
                    seen_selectors.add(sel)
                    mapped_type = {"tel": "phone"}.get(input_type, input_type)
                    f = await self._extract_input(
                        locator, prefix, override_type=mapped_type, ctx=ctx,
                    )
                    fields.append(f)

        # --- Textareas (multiline textboxes) ---
        for locator in await ctx.locator("textarea").all():
            if not await self._is_visible_safe(locator):
                continue
            sel = await self._build_selector(locator, prefix)
            if sel not in seen_selectors:
                seen_selectors.add(sel)
                fields.append(
                    await self._extract_input(locator, prefix, override_type="textarea", ctx=ctx)
                )

        # --- Select / combobox ---
        for role in (self._COMBOBOX_ROLE, self._LISTBOX_ROLE):
            for locator in await ctx.locator(f"role={role}").all():
                if not await self._is_visible_safe(locator):
                    continue
                sel = await self._build_selector(locator, prefix)
                if sel not in seen_selectors:
                    seen_selectors.add(sel)
                    fields.append(await self._extract_select(locator, prefix, ctx=ctx))

        # --- Native <select> not caught by ARIA roles ---
        for locator in await ctx.locator("select").all():
            if not await self._is_visible_safe(locator):
                continue
            sel = await self._build_selector(locator, prefix)
            if sel not in seen_selectors:
                seen_selectors.add(sel)
                fields.append(await self._extract_select(locator, prefix, ctx=ctx))

        # --- Checkboxes ---
        for locator in await ctx.locator(f"role={self._CHECKBOX_ROLE}").all():
            if not await self._is_visible_safe(locator):
                continue
            sel = await self._build_selector(locator, prefix)
            if sel not in seen_selectors:
                seen_selectors.add(sel)
                fields.append(await self._extract_checkbox(locator, prefix, ctx=ctx))

        # --- Radio buttons (grouped) ---
        radio_groups = await self._extract_radio_groups(ctx, prefix)
        for group_field in radio_groups:
            if group_field.locator_desc not in seen_selectors:
                seen_selectors.add(group_field.locator_desc)
                fields.append(group_field)

        # --- File uploads ---
        for locator in await ctx.locator('input[type="file"]').all():
            sel = await self._build_selector(locator, prefix)
            if sel not in seen_selectors:
                seen_selectors.add(sel)
                fields.append(
                    FormField(
                        label=await self._infer_label(locator, ctx),
                        field_type="file",
                        required=await self._is_required(locator),
                        aria_role="file",
                        locator_desc=sel,
                        name_attr=await locator.get_attribute("name"),
                    )
                )

        # --- Spinbuttons (number fields with ARIA role) ---
        for locator in await ctx.locator(f"role={self._SPINBUTTON_ROLE}").all():
            if not await self._is_visible_safe(locator):
                continue
            sel = await self._build_selector(locator, prefix)
            if sel not in seen_selectors:
                seen_selectors.add(sel)
                fields.append(
                    await self._extract_input(locator, prefix, override_type="number", ctx=ctx)
                )

        return fields

    async def _extract_from_iframes(self, page: Page) -> list[FormField]:
        """Detect and extract fields from iframe-embedded forms."""
        fields: list[FormField] = []
        iframes = await page.locator("iframe").all()

        for iframe_loc in iframes:
            src = await iframe_loc.get_attribute("src") or ""
            iframe_id = await iframe_loc.get_attribute("id") or ""
            iframe_name = await iframe_loc.get_attribute("name") or ""

            # Check if this iframe is from a known ATS
            is_ats_iframe = any(pattern in src.lower() for pattern in self.IFRAME_PATTERNS)
            # Also check iframes that might contain forms even without known patterns
            has_form_attr = "apply" in src.lower() or "application" in src.lower()

            if is_ats_iframe or has_form_attr:
                prefix = f"iframe[{iframe_id or iframe_name or src[:50]}]"
                try:
                    iframe_sel = self._build_iframe_selector(iframe_loc, src, iframe_id)
                    frame = page.frame_locator(iframe_sel)
                    iframe_fields = await self._extract_from_context(frame, prefix=prefix)
                    fields.extend(iframe_fields)
                    logger.debug(
                        "Found %d fields in iframe src=%s", len(iframe_fields), src[:80]
                    )
                except Exception:
                    logger.warning("Failed to extract from iframe src=%s", src[:80], exc_info=True)

        return fields

    def _build_iframe_selector(self, locator: Locator, src: str, iframe_id: str) -> str:
        """Build a CSS selector for an iframe element."""
        if iframe_id:
            return f"iframe#{iframe_id}"
        if src:
            # Use a substring match on src
            safe_src = src.split("?")[0]  # Drop query params
            return f'iframe[src*="{safe_src[:60]}"]'
        return "iframe"

    # ---- Individual field extractors ----

    async def _extract_input(
        self,
        locator: Locator,
        prefix: str,
        *,
        override_type: str | None = None,
        ctx: Page | FrameLocator | None = None,
    ) -> FormField:
        """Extract a text-like input field."""
        if ctx is None:
            ctx = self._get_page_from_locator(locator)
        label = await self._infer_label(locator, ctx)
        field_type = override_type or await self._detect_input_type(locator)
        sel = await self._build_selector(locator, prefix)

        current_value: str | None = None
        try:
            current_value = await locator.input_value()
        except Exception:
            pass

        return FormField(
            label=label,
            field_type=field_type,
            required=await self._is_required(locator),
            aria_role=await self._get_aria_role(locator),
            locator_desc=sel,
            current_value=current_value,
            placeholder=await locator.get_attribute("placeholder"),
            name_attr=await locator.get_attribute("name"),
        )

    async def _extract_select(
        self,
        locator: Locator,
        prefix: str,
        *,
        ctx: Page | FrameLocator | None = None,
    ) -> FormField:
        """Extract a select/combobox field with its options."""
        if ctx is None:
            ctx = self._get_page_from_locator(locator)
        label = await self._infer_label(locator, ctx)
        sel = await self._build_selector(locator, prefix)

        options: list[str] = []
        try:
            # Try to get options from child <option> elements
            option_locs = await locator.locator("option").all()
            for opt in option_locs:
                text = (await opt.inner_text()).strip()
                if text:
                    options.append(text)

            # If no <option> children, try ARIA listbox items
            if not options:
                item_locs = await locator.locator("role=option").all()
                for item in item_locs:
                    text = (await item.inner_text()).strip()
                    if text:
                        options.append(text)
        except Exception:
            pass

        return FormField(
            label=label,
            field_type="select",
            required=await self._is_required(locator),
            aria_role=await self._get_aria_role(locator),
            locator_desc=sel,
            options=options,
            name_attr=await locator.get_attribute("name"),
        )

    async def _extract_checkbox(
        self,
        locator: Locator,
        prefix: str,
        *,
        ctx: Page | FrameLocator | None = None,
    ) -> FormField:
        """Extract a checkbox field."""
        if ctx is None:
            ctx = self._get_page_from_locator(locator)
        label = await self._infer_label(locator, ctx)
        sel = await self._build_selector(locator, prefix)

        checked: str | None = None
        try:
            is_checked = await locator.is_checked()
            checked = str(is_checked).lower()
        except Exception:
            pass

        return FormField(
            label=label,
            field_type="checkbox",
            required=await self._is_required(locator),
            aria_role="checkbox",
            locator_desc=sel,
            current_value=checked,
            name_attr=await locator.get_attribute("name"),
        )

    async def _extract_radio_groups(
        self, ctx: Page | FrameLocator, prefix: str
    ) -> list[FormField]:
        """Extract radio button groups, grouping by name attribute."""
        groups: dict[str, list[str]] = {}
        group_labels: dict[str, str] = {}
        group_required: dict[str, bool] = {}

        radio_locs = await ctx.locator(f"role={self._RADIO_ROLE}").all()
        for locator in radio_locs:
            if not await self._is_visible_safe(locator):
                continue
            name = await locator.get_attribute("name") or "unnamed_radio"
            value = await locator.get_attribute("value") or ""

            # Get the label for this specific radio option
            radio_label = await self._infer_label(locator, ctx)

            if name not in groups:
                groups[name] = []
                # Use the first radio's label or fieldset legend as group label
                group_labels[name] = await self._infer_radio_group_label(locator, ctx, name)
                group_required[name] = await self._is_required(locator)

            groups[name].append(radio_label or value)

        fields: list[FormField] = []
        for name, options in groups.items():
            sel = f'{prefix}[name="{name}"]' if prefix else f'[name="{name}"]'
            fields.append(
                FormField(
                    label=group_labels.get(name, name),
                    field_type="radio",
                    required=group_required.get(name, False),
                    aria_role="radiogroup",
                    locator_desc=sel,
                    options=options,
                    name_attr=name,
                )
            )
        return fields

    # ---- Label inference ----

    async def _infer_label(self, locator: Locator, ctx: Page | FrameLocator | None) -> str:
        """Infer the human-readable label for a form element.

        Priority: aria-label > aria-labelledby > associated <label> > placeholder > name.
        """
        # 1. aria-label
        aria_label = await locator.get_attribute("aria-label")
        if aria_label:
            return aria_label.strip()

        # 2. aria-labelledby
        labelledby = await locator.get_attribute("aria-labelledby")
        if labelledby and ctx is not None:
            try:
                label_el = ctx.locator(f"#{labelledby}")
                if await label_el.count() > 0:
                    text = (await label_el.first.inner_text()).strip()
                    if text:
                        return text
            except Exception:
                pass

        # 3. Associated <label for="id">
        el_id = await locator.get_attribute("id")
        if el_id and ctx is not None:
            try:
                label_el = ctx.locator(f'label[for="{el_id}"]')
                if await label_el.count() > 0:
                    text = (await label_el.first.inner_text()).strip()
                    if text:
                        return text
            except Exception:
                pass

        # 4. Parent <label> wrapping the input
        try:
            parent_text: str = await locator.evaluate(
                'el => el.closest("label")?.innerText?.trim() || ""'
            )
            if parent_text:
                return parent_text
        except Exception:
            pass

        # 5. Placeholder
        placeholder = await locator.get_attribute("placeholder")
        if placeholder:
            return placeholder.strip()

        # 6. Title attribute
        title = await locator.get_attribute("title")
        if title:
            return title.strip()

        # 7. Name attribute (last resort)
        name = await locator.get_attribute("name")
        if name:
            return name.replace("_", " ").replace("-", " ").strip()

        return "unknown_field"

    async def _infer_radio_group_label(
        self, locator: Locator, ctx: Page | FrameLocator, name: str
    ) -> str:
        """Try to find the label for a radio group (e.g. fieldset legend)."""
        try:
            legend: str = await locator.evaluate(
                'el => el.closest("fieldset")?.querySelector("legend")?.innerText?.trim() || ""'
            )
            if legend:
                return legend
        except Exception:
            pass
        return await self._infer_label(locator, ctx)

    # ---- Utility methods ----

    async def _detect_input_type(self, locator: Locator) -> str:
        """Detect the semantic type of an input element."""
        input_type = await locator.get_attribute("type")
        if input_type:
            type_map = {
                "email": "email",
                "tel": "phone",
                "url": "url",
                "number": "number",
                "password": "password",
                "date": "date",
                "file": "file",
            }
            if input_type in type_map:
                return type_map[input_type]

        # Check if it's a textarea
        tag: str = await locator.evaluate("el => el.tagName.toLowerCase()")
        if tag == "textarea":
            return "textarea"

        return "text"

    async def _is_required(self, locator: Locator) -> bool:
        """Check if a field is required via HTML or ARIA attributes."""
        required = await locator.get_attribute("required")
        aria_required = await locator.get_attribute("aria-required")
        return required is not None or aria_required == "true"

    async def _get_aria_role(self, locator: Locator) -> str:
        """Get the ARIA role of an element."""
        role = await locator.get_attribute("role")
        if role:
            return role
        try:
            tag: str = await locator.evaluate("el => el.tagName.toLowerCase()")
            return tag
        except Exception:
            return "unknown"

    async def _build_selector(self, locator: Locator, prefix: str = "") -> str:
        """Build a CSS selector to re-locate this element."""
        # Try id first (most stable)
        el_id = await locator.get_attribute("id")
        if el_id:
            sel = f"#{el_id}"
            return f"{prefix} {sel}" if prefix else sel

        # Try name attribute
        name = await locator.get_attribute("name")
        if name:
            sel = f'[name="{name}"]'
            return f"{prefix} {sel}" if prefix else sel

        # Try data-automation-id (Workday)
        data_auto = await locator.get_attribute("data-automation-id")
        if data_auto:
            sel = f'[data-automation-id="{data_auto}"]'
            return f"{prefix} {sel}" if prefix else sel

        # Try data-testid
        testid = await locator.get_attribute("data-testid")
        if testid:
            sel = f'[data-testid="{testid}"]'
            return f"{prefix} {sel}" if prefix else sel

        # Fallback: tag + class
        try:
            fallback: str = await locator.evaluate(
                "el => el.tagName.toLowerCase() + "
                "(el.className ? '.' + el.className.trim().split(/\\s+/).join('.') : '')"
            )
            return f"{prefix} {fallback}" if prefix else fallback
        except Exception:
            return f"{prefix} unknown" if prefix else "unknown"

    async def _is_visible_safe(self, locator: Locator) -> bool:
        """Check visibility, returning False on error."""
        try:
            return await locator.is_visible()
        except Exception:
            return False

    def _get_page_from_locator(self, locator: Locator) -> Page | FrameLocator | None:
        """Attempt to get the page/frame context from a locator."""
        try:
            return locator.page  # type: ignore[return-value]
        except Exception:
            return None
