"""Generic ATS form filler using Playwright (mocked in tests)."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

from backend.auto_apply.profile import ApplicationProfile

# ---------------------------------------------------------------------------
# Field type keywords used to classify form inputs
# ---------------------------------------------------------------------------

_FIELD_TYPE_KEYWORDS: dict[str, list[str]] = {
    "email": ["email", "e-mail", "email_address"],
    "phone": ["phone", "telephone", "mobile", "cell", "tel"],
    "full_name": ["full_name", "name", "first_name", "last_name", "fname", "lname"],
    "linkedin_url": ["linkedin_url", "linkedin", "linked_in"],
    "github_url": ["github_url", "github", "git_hub"],
    "portfolio_url": ["portfolio_url", "portfolio", "website", "personal_website", "url"],
    "location": ["location", "city", "address", "state", "zip", "postal"],
    "work_authorization": ["work_authorization", "work_auth", "authorized", "visa", "citizenship"],
    "years_experience": ["years_experience", "years_of_experience", "experience_years", "years"],
    "education": ["education", "degree", "university", "college", "school", "gpa"],
    "current_title": ["current_title", "job_title", "title", "current_position", "position"],
    "salary": ["salary", "compensation", "pay", "desired_salary", "expected_salary"],
    "file": ["resume", "cv", "upload", "attachment", "file"],
}


def fuzzy_match_label(label: str, candidates: list[str], threshold: int = 80) -> Optional[str]:
    """Match a form field label to a list of profile field candidates using fuzzy matching.

    Returns the best matching candidate or None if no match exceeds the threshold.
    """
    if not candidates or not label:
        return None

    label_lower = label.lower().strip()

    # Try exact keyword match first (faster)
    for candidate in candidates:
        candidate_lower = candidate.lower().replace("_", " ")
        if candidate_lower in label_lower or label_lower in candidate_lower:
            return candidate

    # Check keyword synonyms
    for candidate in candidates:
        keywords = _FIELD_TYPE_KEYWORDS.get(candidate, [candidate])
        for kw in keywords:
            kw_norm = kw.replace("_", " ").lower()
            if kw_norm in label_lower:
                return candidate

    # Fuzzy fallback
    candidate_labels = []
    for candidate in candidates:
        keywords = _FIELD_TYPE_KEYWORDS.get(candidate, [candidate.replace("_", " ")])
        candidate_labels.append(keywords[0].replace("_", " "))

    result = process.extractOne(
        label_lower,
        candidate_labels,
        scorer=fuzz.partial_ratio,
        score_cutoff=threshold,
    )
    if result:
        idx = candidate_labels.index(result[0])
        return candidates[idx]

    return None


def detect_field_type(label: str, element_id: str, input_type: str) -> str:
    """Classify a form field into a semantic type.

    Priority: input_type hint → label/id keyword match → fallback to input_type or 'text'.
    """
    combined = f"{label} {element_id}".lower()

    # Direct input type mappings
    if input_type == "file":
        return "file"
    if input_type == "email":
        return "email"
    if input_type == "tel":
        return "phone"
    if input_type == "url":
        return "portfolio_url"

    # Check each semantic type's keywords
    for field_type, keywords in _FIELD_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw.replace("_", " ") in combined:
                return field_type

    return input_type if input_type else "text"


# ---------------------------------------------------------------------------
# FieldMapping dataclass
# ---------------------------------------------------------------------------


@dataclass
class FieldMapping:
    """Represents a discovered form field and its mapping to a profile key."""

    label: str
    field_type: str
    profile_key: str
    selector: str
    required: bool = False
    field_id: str = ""
    confidence: float = 0.0


# ---------------------------------------------------------------------------
# GenericATSFiller
# ---------------------------------------------------------------------------


class GenericATSFiller:
    """Generic ATS form filler that works across most ATS platforms.

    Uses label/input inspection to map fields to ApplicationProfile keys,
    then fills them with the appropriate values.
    """

    def __init__(self, profile: ApplicationProfile) -> None:
        self.profile = profile
        self._profile_keys = list(ApplicationProfile.__dataclass_fields__.keys())

    async def analyze_form(self, page: Any) -> dict:
        """Inspect a page and return a mapping of discovered fields.

        Returns a dict: { profile_key: FieldMapping }
        """
        mappings: dict[str, FieldMapping] = {}

        try:
            labels = await page.query_selector_all("label")
            for label_el in labels:
                label_text = await label_el.text_content()
                if not label_text:
                    continue
                label_text = label_text.strip()

                # Find associated input via 'for' attribute
                for_attr = await label_el.get_attribute("for")
                if not for_attr:
                    continue

                # Sanitize for_attr to prevent CSS selector injection — allow
                # only alphanumeric characters, hyphens, and underscores.
                safe_for_attr = re.sub(r"[^a-zA-Z0-9_-]", "", for_attr)
                if not safe_for_attr:
                    continue

                input_el = await page.query_selector(f"#{safe_for_attr}, [name='{safe_for_attr}']")
                if input_el is None:
                    continue

                input_type = await input_el.get_attribute("type") or "text"
                input_id = await input_el.get_attribute("id") or ""
                input_name = await input_el.get_attribute("name") or ""

                field_type = detect_field_type(label_text, f"{input_id} {input_name}", input_type)
                matched_key = fuzzy_match_label(label_text, self._profile_keys)

                if matched_key:
                    selector = f"#{safe_for_attr}" if safe_for_attr else f"[name='{input_name}']"
                    mappings[matched_key] = FieldMapping(
                        label=label_text,
                        field_type=field_type,
                        profile_key=matched_key,
                        selector=selector,
                    )
        except Exception as e:
            # Page interaction errors are logged but non-fatal
            logger.warning("analyze_form page interaction error: %s", e)

        return mappings

    async def fill_form(self, page: Any, submit: bool = False) -> dict:
        """Fill the form based on analyzed field mappings.

        Returns a dict of { profile_key: value_filled }.
        """
        mappings = await self.analyze_form(page)
        filled: dict[str, Any] = {}
        skipped: list[str] = []

        profile_dict = self.profile.to_dict()

        for key, mapping in mappings.items():
            value = profile_dict.get(key)
            if value is None:
                skipped.append(key)
                continue

            try:
                if mapping.field_type == "file":
                    # File upload requires special handling (not done here)
                    skipped.append(key)
                    continue

                input_el = await page.query_selector(mapping.selector)
                if input_el:
                    await input_el.fill(str(value))
                    filled[key] = value
            except Exception as e:
                logger.warning("fill_form failed for key %r: %s", key, e)
                skipped.append(key)

        return {"filled": filled, "skipped": skipped}
