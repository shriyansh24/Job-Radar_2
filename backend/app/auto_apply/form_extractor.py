from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from playwright.async_api import FrameLocator, Locator, Page

logger = structlog.get_logger()


@dataclass
class FormField:
    """A structured form field discovered from the page accessibility tree."""

    label: str
    field_type: str
    required: bool
    aria_role: str
    locator_desc: str
    options: list[str] = field(default_factory=list)
    current_value: str | None = None
    placeholder: str | None = None
    name_attr: str | None = None


class FormExtractor:
    """Extract form fields using ARIA-aware locators instead of brittle CSS-only scans."""

    _TEXTBOX_ROLE = "textbox"
    _COMBOBOX_ROLE = "combobox"
    _LISTBOX_ROLE = "listbox"
    _CHECKBOX_ROLE = "checkbox"
    _RADIO_ROLE = "radio"
    _SPINBUTTON_ROLE = "spinbutton"

    IFRAME_PATTERNS: list[str] = [
        "icims",
        "myworkdayjobs",
        "lever.co",
        "ashbyhq",
    ]

    async def extract_fields(self, page: Page) -> list[FormField]:
        fields: list[FormField] = []
        fields.extend(await self._extract_from_context(page))

        iframe_fields = await self._extract_from_iframes(page)
        fields.extend(iframe_fields)

        logger.info(
            "auto_apply_form_fields_extracted",
            total=len(fields),
            iframe_fields=len(iframe_fields),
        )
        return fields

    async def _extract_from_context(
        self, ctx: Page | FrameLocator, prefix: str = ""
    ) -> list[FormField]:
        fields: list[FormField] = []
        seen_selectors: set[str] = set()

        for locator in await ctx.locator("role=textbox").all():
            if not await self._is_visible_safe(locator):
                continue
            field = await self._extract_input(locator, prefix, ctx=ctx)
            if field.locator_desc not in seen_selectors:
                seen_selectors.add(field.locator_desc)
                fields.append(field)

        for input_type in ("email", "tel", "url", "number"):
            for locator in await ctx.locator(f'input[type="{input_type}"]').all():
                if not await self._is_visible_safe(locator):
                    continue
                selector = await self._build_selector(locator, prefix)
                if selector in seen_selectors:
                    continue
                seen_selectors.add(selector)
                mapped_type = {"tel": "phone"}.get(input_type, input_type)
                fields.append(
                    await self._extract_input(
                        locator,
                        prefix,
                        override_type=mapped_type,
                        ctx=ctx,
                    )
                )

        for locator in await ctx.locator("textarea").all():
            if not await self._is_visible_safe(locator):
                continue
            selector = await self._build_selector(locator, prefix)
            if selector in seen_selectors:
                continue
            seen_selectors.add(selector)
            fields.append(
                await self._extract_input(locator, prefix, override_type="textarea", ctx=ctx)
            )

        for role in (self._COMBOBOX_ROLE, self._LISTBOX_ROLE):
            for locator in await ctx.locator(f"role={role}").all():
                if not await self._is_visible_safe(locator):
                    continue
                selector = await self._build_selector(locator, prefix)
                if selector in seen_selectors:
                    continue
                seen_selectors.add(selector)
                fields.append(await self._extract_select(locator, prefix, ctx=ctx))

        for locator in await ctx.locator("select").all():
            if not await self._is_visible_safe(locator):
                continue
            selector = await self._build_selector(locator, prefix)
            if selector in seen_selectors:
                continue
            seen_selectors.add(selector)
            fields.append(await self._extract_select(locator, prefix, ctx=ctx))

        for locator in await ctx.locator(f"role={self._CHECKBOX_ROLE}").all():
            if not await self._is_visible_safe(locator):
                continue
            selector = await self._build_selector(locator, prefix)
            if selector in seen_selectors:
                continue
            seen_selectors.add(selector)
            fields.append(await self._extract_checkbox(locator, prefix, ctx=ctx))

        radio_groups = await self._extract_radio_groups(ctx, prefix)
        for group_field in radio_groups:
            if group_field.locator_desc in seen_selectors:
                continue
            seen_selectors.add(group_field.locator_desc)
            fields.append(group_field)

        for locator in await ctx.locator('input[type="file"]').all():
            selector = await self._build_selector(locator, prefix)
            if selector in seen_selectors:
                continue
            seen_selectors.add(selector)
            fields.append(
                FormField(
                    label=await self._infer_label(locator, ctx),
                    field_type="file",
                    required=await self._is_required(locator),
                    aria_role="file",
                    locator_desc=selector,
                    name_attr=await locator.get_attribute("name"),
                )
            )

        for locator in await ctx.locator(f"role={self._SPINBUTTON_ROLE}").all():
            if not await self._is_visible_safe(locator):
                continue
            selector = await self._build_selector(locator, prefix)
            if selector in seen_selectors:
                continue
            seen_selectors.add(selector)
            fields.append(
                await self._extract_input(locator, prefix, override_type="number", ctx=ctx)
            )

        return fields

    async def _extract_from_iframes(self, page: Page) -> list[FormField]:
        fields: list[FormField] = []
        iframes = await page.locator("iframe").all()

        for iframe_loc in iframes:
            src = await iframe_loc.get_attribute("src") or ""
            iframe_id = await iframe_loc.get_attribute("id") or ""
            iframe_name = await iframe_loc.get_attribute("name") or ""
            is_ats_iframe = any(pattern in src.lower() for pattern in self.IFRAME_PATTERNS)
            has_application_hint = "apply" in src.lower() or "application" in src.lower()

            if not is_ats_iframe and not has_application_hint:
                continue

            prefix = f"iframe[{iframe_id or iframe_name or src[:50]}]"
            try:
                iframe_selector = self._build_iframe_selector(src=src, iframe_id=iframe_id)
                frame = page.frame_locator(iframe_selector)
                iframe_fields = await self._extract_from_context(frame, prefix=prefix)
                fields.extend(iframe_fields)
                logger.debug(
                    "auto_apply_iframe_fields_extracted",
                    src=src[:120],
                    count=len(iframe_fields),
                )
            except Exception as exc:
                logger.warning(
                    "auto_apply_iframe_field_extraction_failed",
                    src=src[:120],
                    error=str(exc),
                )

        return fields

    def _build_iframe_selector(self, *, src: str, iframe_id: str) -> str:
        if iframe_id:
            return f"iframe#{iframe_id}"
        if src:
            safe_src = src.split("?")[0]
            return f'iframe[src*="{safe_src[:60]}"]'
        return "iframe"

    async def _extract_input(
        self,
        locator: Locator,
        prefix: str,
        *,
        override_type: str | None = None,
        ctx: Page | FrameLocator | None = None,
    ) -> FormField:
        label = await self._infer_label(locator, ctx)
        field_type = override_type or await self._detect_input_type(locator)
        selector = await self._build_selector(locator, prefix)

        current_value: str | None = None
        try:
            current_value = await locator.input_value()
        except Exception:
            logger.debug("auto_apply_field_input_value_unavailable", selector=selector)

        return FormField(
            label=label,
            field_type=field_type,
            required=await self._is_required(locator),
            aria_role=await self._get_aria_role(locator),
            locator_desc=selector,
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
        label = await self._infer_label(locator, ctx)
        selector = await self._build_selector(locator, prefix)

        options: list[str] = []
        try:
            option_locs = await locator.locator("option").all()
            for option in option_locs:
                text = (await option.inner_text()).strip()
                if text:
                    options.append(text)
            if not options:
                option_locs = await locator.locator("role=option").all()
                for option in option_locs:
                    text = (await option.inner_text()).strip()
                    if text:
                        options.append(text)
        except Exception as exc:
            logger.debug(
                "auto_apply_select_options_unavailable",
                selector=selector,
                error=str(exc),
            )

        return FormField(
            label=label,
            field_type="select",
            required=await self._is_required(locator),
            aria_role=await self._get_aria_role(locator),
            locator_desc=selector,
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
        label = await self._infer_label(locator, ctx)
        selector = await self._build_selector(locator, prefix)

        checked: str | None = None
        try:
            checked = str(await locator.is_checked()).lower()
        except Exception:
            logger.debug("auto_apply_checkbox_state_unavailable", selector=selector)

        return FormField(
            label=label,
            field_type="checkbox",
            required=await self._is_required(locator),
            aria_role="checkbox",
            locator_desc=selector,
            current_value=checked,
            name_attr=await locator.get_attribute("name"),
        )

    async def _extract_radio_groups(
        self, ctx: Page | FrameLocator, prefix: str
    ) -> list[FormField]:
        groups: dict[str, list[str]] = {}
        labels: dict[str, str] = {}
        required: dict[str, bool] = {}

        for locator in await ctx.locator(f"role={self._RADIO_ROLE}").all():
            if not await self._is_visible_safe(locator):
                continue

            name = await locator.get_attribute("name") or "unnamed_radio"
            option_label = await self._infer_label(locator, ctx)

            if name not in groups:
                groups[name] = []
                labels[name] = await self._infer_radio_group_label(locator, ctx)
                required[name] = await self._is_required(locator)

            groups[name].append(option_label or await locator.get_attribute("value") or "")

        fields: list[FormField] = []
        for name, options in groups.items():
            selector = f'{prefix}[name="{name}"]' if prefix else f'[name="{name}"]'
            fields.append(
                FormField(
                    label=labels.get(name, name),
                    field_type="radio",
                    required=required.get(name, False),
                    aria_role="radiogroup",
                    locator_desc=selector,
                    options=options,
                    name_attr=name,
                )
            )
        return fields

    async def _infer_label(
        self, locator: Locator, ctx: Page | FrameLocator | None = None
    ) -> str:
        aria_label = await locator.get_attribute("aria-label")
        if aria_label:
            return aria_label.strip()

        labelled_by = await locator.get_attribute("aria-labelledby")
        if labelled_by and ctx is not None:
            try:
                label_el = ctx.locator(f"#{labelled_by}")
                if await label_el.count() > 0:
                    text = (await label_el.first.inner_text()).strip()
                    if text:
                        return text
            except Exception:
                logger.debug(
                    "auto_apply_aria_labelledby_lookup_failed",
                    labelledby=labelled_by,
                )

        element_id = await locator.get_attribute("id")
        if element_id and ctx is not None:
            try:
                label_el = ctx.locator(f'label[for="{element_id}"]')
                if await label_el.count() > 0:
                    text = (await label_el.first.inner_text()).strip()
                    if text:
                        return text
            except Exception:
                logger.debug("auto_apply_label_for_lookup_failed", element_id=element_id)

        try:
            parent_text: str = await locator.evaluate(
                'el => el.closest("label")?.innerText?.trim() || ""'
            )
            if parent_text:
                return parent_text
        except Exception:
            logger.debug("auto_apply_parent_label_lookup_failed")

        placeholder = await locator.get_attribute("placeholder")
        if placeholder:
            return placeholder.strip()

        title = await locator.get_attribute("title")
        if title:
            return title.strip()

        name = await locator.get_attribute("name")
        if name:
            return name.replace("_", " ").replace("-", " ").strip()

        return "unknown_field"

    async def _infer_radio_group_label(self, locator: Locator, ctx: Page | FrameLocator) -> str:
        try:
            legend: str = await locator.evaluate(
                'el => el.closest("fieldset")?.querySelector("legend")?.innerText?.trim() || ""'
            )
            if legend:
                return legend
        except Exception:
            logger.debug("auto_apply_radio_group_legend_lookup_failed")
        return await self._infer_label(locator, ctx)

    async def _detect_input_type(self, locator: Locator) -> str:
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

        try:
            tag: str = await locator.evaluate("el => el.tagName.toLowerCase()")
            if tag == "textarea":
                return "textarea"
        except Exception:
            logger.debug("auto_apply_input_tag_detection_failed")

        return "text"

    async def _is_required(self, locator: Locator) -> bool:
        required = await locator.get_attribute("required")
        aria_required = await locator.get_attribute("aria-required")
        return required is not None or aria_required == "true"

    async def _get_aria_role(self, locator: Locator) -> str:
        role = await locator.get_attribute("role")
        if role:
            return role
        try:
            return await locator.evaluate("el => el.tagName.toLowerCase()")
        except Exception:
            logger.debug("auto_apply_aria_role_detection_failed")
            return "unknown"

    async def _build_selector(self, locator: Locator, prefix: str = "") -> str:
        element_id = await locator.get_attribute("id")
        if element_id:
            selector = f"#{element_id}"
            return f"{prefix} {selector}" if prefix else selector

        name = await locator.get_attribute("name")
        if name:
            selector = f'[name="{name}"]'
            return f"{prefix} {selector}" if prefix else selector

        data_automation_id = await locator.get_attribute("data-automation-id")
        if data_automation_id:
            selector = f'[data-automation-id="{data_automation_id}"]'
            return f"{prefix} {selector}" if prefix else selector

        testid = await locator.get_attribute("data-testid")
        if testid:
            selector = f'[data-testid="{testid}"]'
            return f"{prefix} {selector}" if prefix else selector

        try:
            fallback: str = await locator.evaluate(
                "el => el.tagName.toLowerCase() + "
                "(el.className ? '.' + el.className.trim().split(/\\s+/).join('.') : '')"
            )
            return f"{prefix} {fallback}" if prefix else fallback
        except Exception:
            logger.debug("auto_apply_fallback_selector_failed")
            return f"{prefix} unknown".strip() if prefix else "unknown"

    async def _is_visible_safe(self, locator: Locator) -> bool:
        try:
            return await locator.is_visible()
        except Exception:
            return False
