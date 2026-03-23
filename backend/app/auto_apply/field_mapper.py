"""3-tier field mapping engine: regex patterns -> DB lookup -> LLM classification.

Maps extracted FormField instances to semantic profile keys so the auto-apply
system knows which user data to fill into each form field.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.auto_apply.form_extractor import FormField

if TYPE_CHECKING:
    from app.enrichment.llm_client import LLMClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# EEOC default value — always used for demographic/EEO fields
# ---------------------------------------------------------------------------
EEOC_DEFAULT = "Prefer not to answer"

# ---------------------------------------------------------------------------
# 120+ compiled regex patterns: field label -> semantic profile key
#
# Ordering matters: more specific patterns come first to avoid greedy matches.
# Keys prefixed with ``__eeoc_`` are demographic fields that always receive
# the ``EEOC_DEFAULT`` value rather than profile data.
# ---------------------------------------------------------------------------
_RAW_PATTERNS: dict[str, str] = {
    # ---- Name fields ----
    r"(?i)\bfirst\s*name\b": "first_name",
    r"(?i)\blast\s*name\b": "last_name",
    r"(?i)\b(sur|family)\s*name\b": "last_name",
    r"(?i)\bgiven\s*name\b": "first_name",
    r"(?i)\bfull\s*name\b": "full_name",
    r"(?i)\bmiddle\s*(name|initial)\b": "middle_name",
    r"(?i)\bpreferred\s*name\b": "preferred_name",
    r"(?i)\blegal\s*name\b": "full_name",
    r"(?i)\bname\s*prefix\b": "name_prefix",
    r"(?i)\bname\s*suffix\b": "name_suffix",
    # ---- Contact ----
    r"(?i)\be[\-\.]?mail\s*(address)?\b": "email",
    r"(?i)\bphone\s*(number)?\b": "phone",
    r"(?i)\bmobile\s*(number|phone)?\b": "phone",
    r"(?i)\bcell\s*(phone|number)?\b": "phone",
    r"(?i)\bhome\s*phone\b": "phone",
    r"(?i)\bwork\s*phone\b": "work_phone",
    r"(?i)\bfax\b": "fax",
    # ---- Address ----
    r"(?i)\bstreet\s*(address)?\b": "street_address",
    r"(?i)\baddress\s*(line)?\s*1\b": "address_line1",
    r"(?i)\baddress\s*(line)?\s*2\b": "address_line2",
    r"(?i)\bapartment|apt|suite|unit\b": "address_line2",
    r"(?i)\bcity\b": "city",
    r"(?i)\bstate\b(?!ment)": "state",
    r"(?i)\bprovince\b": "state",
    r"(?i)\bregion\b": "state",
    r"(?i)\bzip\s*(code)?\b": "zip_code",
    r"(?i)\bpostal\s*(code)?\b": "zip_code",
    r"(?i)\bcountry\b": "country",
    # ---- Links / URLs ----
    r"(?i)\blinkedin\b": "linkedin_url",
    r"(?i)\bgithub\b": "github_url",
    r"(?i)\bgitlab\b": "gitlab_url",
    r"(?i)\bportfolio\b": "website_url",
    r"(?i)\bpersonal\s*(web)?site\b": "website_url",
    r"(?i)\bwebsite\s*(url)?\b": "website_url",
    r"(?i)\bblog\b": "blog_url",
    r"(?i)\btwitter|x\.com\b": "twitter_url",
    r"(?i)\bstack\s*overflow\b": "stackoverflow_url",
    r"(?i)\bdribbble\b": "dribbble_url",
    r"(?i)\bbehance\b": "behance_url",
    # ---- Current position ----
    r"(?i)\bcurrent\s*(company|employer|organization)\b": "current_company",
    r"(?i)\bcurrent\s*(job\s*)?title\b": "current_title",
    r"(?i)\bjob\s*title\b": "current_title",
    r"(?i)\bposition\s*title\b": "current_title",
    r"(?i)\brole\b": "current_title",
    r"(?i)\bheadline\b": "headline",
    # ---- Experience ----
    r"(?i)\byears?\s*(of\s*)?experience\b": "years_experience",
    r"(?i)\btotal\s*experience\b": "years_experience",
    r"(?i)\bwork\s*experience\b": "years_experience",
    r"(?i)\bprofessional\s*experience\b": "years_experience",
    r"(?i)\bexperience\s*level\b": "experience_level",
    r"(?i)\bseniority\b": "experience_level",
    # ---- Salary ----
    r"(?i)\bsalary\s*(expectation|requirement|desired|range)?\b": "desired_salary",
    r"(?i)\bdesired\s*(salary|compensation|pay)\b": "desired_salary",
    r"(?i)\bexpected\s*(salary|compensation|pay)\b": "desired_salary",
    r"(?i)\bcompensation\s*(expectation|requirement)?\b": "desired_salary",
    r"(?i)\bminimum\s*salary\b": "minimum_salary",
    r"(?i)\bcurrent\s*salary\b": "current_salary",
    r"(?i)\bpay\s*rate\b": "desired_salary",
    # ---- Availability / relocation ----
    r"(?i)\bwilling\s*to\s*relocate\b": "willing_to_relocate",
    r"(?i)\bopen\s*to\s*relocation\b": "willing_to_relocate",
    r"(?i)\brelocation\b": "willing_to_relocate",
    r"(?i)\bstart\s*date\b": "start_date",
    r"(?i)\bavailable\s*(from|date|to\s*start)\b": "start_date",
    r"(?i)\bdate\s*available\b": "start_date",
    r"(?i)\bearliest\s*start\b": "start_date",
    r"(?i)\bnotice\s*period\b": "notice_period",
    # ---- Work authorization ----
    r"(?i)\bauthori[sz]ed\s*to\s*work\b": "work_authorization",
    r"(?i)\bwork\s*authori[sz]ation\b": "work_authorization",
    r"(?i)\blegally?\s*(authori[sz]ed|eligible|permitted)\b": "work_authorization",
    r"(?i)\belig(ible|ibility)\s*to\s*work\b": "work_authorization",
    r"(?i)\brequire\s*sponsor(ship)?\b": "requires_sponsorship",
    r"(?i)\bvisa\s*sponsor(ship)?\b": "requires_sponsorship",
    r"(?i)\bneed\s*sponsor(ship)?\b": "requires_sponsorship",
    r"(?i)\bimmigration\s*status\b": "work_authorization",
    r"(?i)\bvisa\s*status\b": "work_authorization",
    r"(?i)\bwork\s*permit\b": "work_authorization",
    r"(?i)\bcitizenship\b": "citizenship",
    # ---- Education ----
    r"(?i)\bhighest?\s*(degree|education|level)\b": "highest_degree",
    r"(?i)\bdegree\s*(type|level|earned)?\b": "highest_degree",
    r"(?i)\beducation\s*(level)?\b": "highest_degree",
    r"(?i)\bschool\s*(name)?\b": "school_name",
    r"(?i)\buniversity\b": "school_name",
    r"(?i)\bcollege\b": "school_name",
    r"(?i)\binstitution\b": "school_name",
    r"(?i)\bgpa|grade\s*point\b": "gpa",
    r"(?i)\bgraduat(ion|e|ed)\s*(date|year)?\b": "graduation_date",
    r"(?i)\bmajor\b": "major",
    r"(?i)\bfield\s*of\s*study\b": "major",
    r"(?i)\bconcentration\b": "major",
    r"(?i)\bminor\b": "minor",
    r"(?i)\bcertification(s)?\b": "certifications",
    r"(?i)\blicense(s)?\b": "licenses",
    # ---- Documents / uploads ----
    r"(?i)\bresume\b": "resume_file",
    r"(?i)\bcv\b": "resume_file",
    r"(?i)\bcurriculum\s*vitae\b": "resume_file",
    r"(?i)\bcover\s*letter\b": "cover_letter",
    r"(?i)\bwriting\s*sample\b": "writing_sample",
    r"(?i)\btranscript\b": "transcript",
    r"(?i)\bwork\s*sample\b": "work_sample",
    r"(?i)\badditional\s*(document|attachment|file)\b": "additional_document",
    # ---- Skills / languages ----
    r"(?i)\bskill(s)?\b": "skills",
    r"(?i)\blanguage(s)?\s*(spoken|proficien)?\b": "languages",
    r"(?i)\bprogramming\s*language(s)?\b": "programming_languages",
    r"(?i)\btechnolog(y|ies)\b": "technologies",
    r"(?i)\btool(s)?\b": "tools",
    # ---- References ----
    r"(?i)\breference\s*(name)?\b": "reference_name",
    r"(?i)\breference\s*(email|e-?mail)\b": "reference_email",
    r"(?i)\breference\s*(phone|number)\b": "reference_phone",
    r"(?i)\breference\s*(title|position)\b": "reference_title",
    r"(?i)\breference\s*(company|organization)\b": "reference_company",
    r"(?i)\brelationship\s*(to\s*reference)?\b": "reference_relationship",
    # ---- Source / how did you hear ----
    r"(?i)\bhow\s*did\s*you\s*(hear|find|learn)\b": "source",
    r"(?i)\breferral\s*(source|name)?\b": "referral_source",
    r"(?i)\breferr(ed|al)\s*by\b": "referred_by",
    r"(?i)\bsource\b": "source",
    # ---- Open-ended ----
    r"(?i)\bwhy\s*(do\s*you\s*want|are\s*you\s*interested)\b": "motivation",
    r"(?i)\badditional\s*(information|comments|notes)\b": "additional_info",
    r"(?i)\banything\s*else\b": "additional_info",
    r"(?i)\bsummary\b": "summary",
    r"(?i)\bobjective\b": "objective",
    # ---- EEOC / demographic fields (always "Prefer not to answer") ----
    r"(?i)\bgender\s*(identity)?\b": "__eeoc_gender",
    r"(?i)\bsex\b": "__eeoc_gender",
    r"(?i)\bpronoun(s)?\b": "__eeoc_pronouns",
    r"(?i)\brace\b": "__eeoc_race",
    r"(?i)\bethnicit(y|ies)\b": "__eeoc_race",
    r"(?i)\bhispanic\s*(or\s*latino)?\b": "__eeoc_race",
    r"(?i)\bveteran\s*(status)?\b": "__eeoc_veteran",
    r"(?i)\bmilitary\s*(service|status)\b": "__eeoc_veteran",
    r"(?i)\bprotected\s*veteran\b": "__eeoc_veteran",
    r"(?i)\bdisabilit(y|ies)\s*(status)?\b": "__eeoc_disability",
    r"(?i)\bhandicap\b": "__eeoc_disability",
    r"(?i)\baccommodation(s)?\b": "__eeoc_disability",
    r"(?i)\bsexual\s*orientation\b": "__eeoc_sexual_orientation",
    r"(?i)\bmarital\s*status\b": "__eeoc_marital_status",
    r"(?i)\bdate\s*of\s*birth\b": "__eeoc_dob",
    r"(?i)\bage\b": "__eeoc_age",
    r"(?i)\breligio(n|us)\b": "__eeoc_religion",
    r"(?i)\bnational\s*origin\b": "__eeoc_national_origin",
    # ---- Misc ----
    r"(?i)\bsocial\s*security\b": "__pii_ssn",
    r"(?i)\bssn\b": "__pii_ssn",
    r"(?i)\bdriver.?s?\s*license\b": "__pii_drivers_license",
    r"(?i)\bbackground\s*check\b": "background_check_consent",
    r"(?i)\bdrug\s*(test|screen)\b": "drug_test_consent",
    r"(?i)\bnon[\-\s]?compete\b": "non_compete_agreement",
    r"(?i)\bconfidentialit(y|al)\b": "confidentiality_agreement",
}

# Pre-compile all patterns for performance
FIELD_PATTERNS: dict[re.Pattern[str], str] = {
    re.compile(pattern): key for pattern, key in _RAW_PATTERNS.items()
}


@dataclass
class MappedField:
    """Result of mapping an extracted form field to a semantic profile key."""

    field: FormField
    semantic_key: str | None
    confidence: float  # 0.0 - 1.0
    # "tier1_regex", "tier2_db", "tier3_llm", "eeoc_default", "pii_blocked", "unmatched"
    source_tier: str
    value: str


class FieldMapper:
    """3-tier field mapping engine.

    Tier 1: Regex pattern matching against field label/name/placeholder.
    Tier 2: DB lookup (stub — returns None, to be filled in C7).
    Tier 3: LLM classification (stub — returns None, to be filled later).
    """

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm = llm_client
        self._db_cache: dict[str, str] = {}  # Populated from FieldMappingRule table in C7

    async def map_fields(
        self, fields: list[FormField], profile: dict[str, str]
    ) -> list[MappedField]:
        """Map a list of extracted form fields to profile values.

        Args:
            fields: Extracted form fields from FormExtractor.
            profile: Flat dict mapping semantic keys to user values.

        Returns:
            List of MappedField with resolved values and confidence scores.
        """
        results: list[MappedField] = []
        for field in fields:
            mapped = await self._resolve_field(field, profile)
            results.append(mapped)
        return results

    async def _resolve_field(
        self, field: FormField, profile: dict[str, str]
    ) -> MappedField:
        """Resolve a single field through the 3-tier cascade."""
        # Build a combined text from all identifying attributes
        search_texts = self._get_search_texts(field)

        # Tier 1: Regex pattern matching
        semantic_key = self._tier1_regex(search_texts)
        if semantic_key is not None:
            return self._build_mapped_field(field, semantic_key, "tier1_regex", profile)

        # Tier 2: DB lookup (stub for C7)
        semantic_key = self._tier2_db_lookup(search_texts)
        if semantic_key is not None:
            return self._build_mapped_field(field, semantic_key, "tier2_db", profile)

        # Tier 3: LLM classification (stub)
        semantic_key = await self._tier3_llm_classify(field)
        if semantic_key is not None:
            return self._build_mapped_field(field, semantic_key, "tier3_llm", profile)

        # Unmatched
        return MappedField(
            field=field,
            semantic_key=None,
            confidence=0.0,
            source_tier="unmatched",
            value="",
        )

    def _get_search_texts(self, field: FormField) -> list[str]:
        """Collect all text sources from a field for pattern matching."""
        texts: list[str] = []
        if field.label and field.label != "unknown_field":
            texts.append(field.label)
        if field.name_attr:
            # Convert name_attr to readable form: "first_name" -> "first name"
            texts.append(field.name_attr.replace("_", " ").replace("-", " "))
        if field.placeholder:
            texts.append(field.placeholder)
        return texts

    def _tier1_regex(self, search_texts: list[str]) -> str | None:
        """Tier 1: Match field text against compiled regex patterns."""
        for text in search_texts:
            for pattern, semantic_key in FIELD_PATTERNS.items():
                if pattern.search(text):
                    return semantic_key
        return None

    def _tier2_db_lookup(self, search_texts: list[str]) -> str | None:
        """Tier 2: Look up field label in database cache.

        Stub implementation — returns None. Will be populated from
        FieldMappingRule table in C7.
        """
        for text in search_texts:
            result = self._db_cache.get(text.lower().strip())
            if result:
                return result
        return None

    async def _tier3_llm_classify(self, field: FormField) -> str | None:
        """Tier 3: Use LLM to classify unknown fields.

        Stub implementation — returns None. Will be implemented when
        LLM classification is wired up.
        """
        return None

    def _build_mapped_field(
        self,
        field: FormField,
        semantic_key: str,
        source_tier: str,
        profile: dict[str, str],
    ) -> MappedField:
        """Build a MappedField, handling EEOC and PII special keys."""
        # EEOC fields always get the default value
        if semantic_key.startswith("__eeoc_"):
            return MappedField(
                field=field,
                semantic_key=semantic_key,
                confidence=1.0,
                source_tier="eeoc_default",
                value=EEOC_DEFAULT,
            )

        # PII fields should never be auto-filled
        if semantic_key.startswith("__pii_"):
            return MappedField(
                field=field,
                semantic_key=semantic_key,
                confidence=1.0,
                source_tier="pii_blocked",
                value="",
            )

        # Normal field — look up in profile
        value = profile.get(semantic_key, "")
        confidence = self._get_confidence(source_tier)

        return MappedField(
            field=field,
            semantic_key=semantic_key,
            confidence=confidence,
            source_tier=source_tier,
            value=value,
        )

    @staticmethod
    def _get_confidence(source_tier: str) -> float:
        """Return confidence score based on the mapping source."""
        return {
            "tier1_regex": 0.95,
            "tier2_db": 0.85,
            "tier3_llm": 0.70,
        }.get(source_tier, 0.0)

    def load_db_cache(self, mappings: dict[str, str]) -> None:
        """Load field mappings from the database into the cache.

        Args:
            mappings: Dict of lowercase label -> semantic_key from DB.
        """
        self._db_cache = {k.lower().strip(): v for k, v in mappings.items()}
