from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.async_api import Page

    from app.auto_apply.models import AutoApplyProfile
    from app.enrichment.llm_client import LLMClient


class GenericATSFiller:
    """Fill common application form fields using Playwright."""

    def __init__(self, page: Page, profile: AutoApplyProfile, llm_client: LLMClient | None):
        self.page = page
        self.profile = profile
        self.llm = llm_client
        self.filled_fields: dict[str, str] = {}
        self.missed_fields: list[str] = []

    async def fill_form(self) -> dict[str, Any]:
        """Detect form fields and fill them."""
        fields = await self._detect_fields()

        for field in fields:
            value = await self._get_value_for_field(field)
            if value:
                await self._fill_field(field, value)
                self.filled_fields[field["label"]] = value
            else:
                self.missed_fields.append(field["label"])

        return {
            "filled": self.filled_fields,
            "missed": self.missed_fields,
        }

    async def _detect_fields(self) -> list[dict[str, Any]]:
        """Find all form fields with their labels."""
        fields: list[dict[str, Any]] = []

        inputs = await self.page.query_selector_all(
            "input:visible, select:visible, textarea:visible"
        )
        for inp in inputs:
            field_type = await inp.get_attribute("type") or "text"
            name = await inp.get_attribute("name") or ""
            label_text = await self._get_label_for_element(inp)
            placeholder = await inp.get_attribute("placeholder") or ""

            fields.append(
                {
                    "element": inp,
                    "type": field_type,
                    "name": name,
                    "label": label_text or placeholder or name,
                    "tag": await inp.evaluate("el => el.tagName.toLowerCase()"),
                }
            )

        return fields

    async def _get_value_for_field(self, field: dict[str, Any]) -> str | None:
        """Match field to profile data."""
        label = field["label"].lower()

        first_name = (
            (self.profile.full_name or "").split()[0] if self.profile.full_name else None
        )
        last_name = (
            (self.profile.full_name or "").split()[-1]
            if self.profile.full_name and " " in self.profile.full_name
            else None
        )

        mappings: dict[str, str | None] = {
            "name": self.profile.full_name,
            "full name": self.profile.full_name,
            "first name": first_name,
            "last name": last_name,
            "email": self.profile.email,
            "phone": self.profile.phone,
            "linkedin": self.profile.linkedin_url,
            "github": self.profile.github_url,
            "portfolio": self.profile.portfolio_url,
            "website": self.profile.portfolio_url,
        }

        for key, value in mappings.items():
            if key in label and value:
                return value

        # For unknown fields, use LLM to figure out what to fill
        if self.llm and field["type"] not in ("file", "hidden", "submit"):
            return await self._llm_fill(field)

        return None

    async def _llm_fill(self, field: dict[str, Any]) -> str | None:
        """Use LLM to determine appropriate field value."""
        prompt = (
            f"Given this application form field, what should I fill in?\n"
            f"Field label: {field['label']}\n"
            f"Field type: {field['type']}\n"
            f"My profile: Name={self.profile.full_name}, Email={self.profile.email}\n\n"
            f'Return ONLY the value to fill in, or "SKIP" if you can\'t determine it.'
        )
        try:
            response = await self.llm.chat(
                [{"role": "user", "content": prompt}], temperature=0.1, max_tokens=100
            )
            if response.strip().upper() == "SKIP":
                return None
            return response.strip()
        except Exception:
            return None

    async def _fill_field(self, field: dict[str, Any], value: str) -> None:
        """Fill a single field."""
        element = field["element"]
        tag = field["tag"]

        if tag == "select":
            await element.select_option(label=value)
        elif field["type"] == "file":
            await element.set_input_files(value)
        elif field["type"] in ("checkbox", "radio"):
            if value.lower() in ("true", "yes", "1"):
                await element.check()
        else:
            await element.fill(value)

    async def _get_label_for_element(self, element: Any) -> str:
        """Find the label text for a form element."""
        # Try aria-label
        aria = await element.get_attribute("aria-label")
        if aria:
            return aria
        # Try associated <label>
        el_id = await element.get_attribute("id")
        if el_id:
            label = await self.page.query_selector(f'label[for="{el_id}"]')
            if label:
                return await label.inner_text()
        # Try parent label
        parent_label: str = await element.evaluate(
            'el => el.closest("label")?.innerText || ""'
        )
        return parent_label
