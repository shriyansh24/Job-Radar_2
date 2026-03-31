"""Email parser for job-related email classification and entity extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ParsedEmail:
    action: str  # rejection, interview, offer, outreach
    confidence: float
    company: str | None = None
    job_title: str | None = None
    dates: list[datetime] = field(default_factory=list)
    details: dict[str, str] = field(default_factory=dict)
    ats_source: str | None = None  # greenhouse, lever, workday, icims


# ATS sender domain patterns
_ATS_DOMAINS: dict[str, str] = {
    "greenhouse.io": "greenhouse",
    "greenhouse-mail.io": "greenhouse",
    "lever.co": "lever",
    "myworkdayjobs.com": "workday",
    "myworkday.com": "workday",
    "icims.com": "icims",
}

# Ordered by priority: offer > interview > rejection > outreach
_OFFER_PATTERNS: list[str] = [
    r"pleased to (?:extend|offer)",
    r"offer (?:letter|of employment)",
    r"compensation package",
    r"we(?:'d| would) like to (?:extend|offer)",
    r"excited to (?:welcome|offer)",
    r"formal offer",
    r"contingent offer",
]

_INTERVIEW_PATTERNS: list[str] = [
    r"(?:schedule|scheduling).*interview",
    r"(?:like|love) to invite you",
    r"meet with.*team",
    r"next steps.*interview",
    r"phone screen",
    r"technical assessment",
    r"coding challenge",
    r"take[- ]home",
    r"on[- ]site (?:interview|visit)",
    r"panel interview",
    r"video (?:call|interview)",
    r"calendar invite.*interview",
    r"interview confirmation",
    r"(?:virtual|in-person) interview",
]

_REJECTION_PATTERNS: list[str] = [
    r"unfortunately.*not.*(?:moving|proceed)",
    r"decided not to (?:proceed|move)",
    r"other candidates.*more closely",
    r"(?:won't|will not) be (?:moving|proceeding) forward",
    r"position has been filled",
    r"not a (?:match|fit) at this time",
    r"after careful (?:consideration|review)",
    r"we (?:have|'ve) decided to (?:move|go) (?:forward )?with",
    r"regret to inform",
    r"unable to offer.*(?:position|role)",
    r"we appreciate your interest.*(?:however|but)",
]

_OUTREACH_PATTERNS: list[str] = [
    r"(?:found|saw) your (?:profile|resume)",
    r"(?:interested|exciting) (?:opportunity|role|position)",
    r"would you be (?:open|interested)",
    r"reaching out.*(?:role|position|opportunity)",
    r"we(?:'re| are) (?:hiring|looking for)",
    r"great fit for",
    r"your (?:background|experience).*(?:caught|stood out)",
]

# Date extraction pattern (common formats)
_DATE_PATTERN = re.compile(
    r"(?:"
    r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*)?"
    r"(?:"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2}(?:,?\s+\d{4})?)"
    r"|(?:\d{1,2}/\d{1,2}/\d{2,4})"
    r"|(?:\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)

_MONTH_MAP: dict[str, int] = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

# Job title extraction: "for the <title> position/role"
_TITLE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"(?:for (?:the|our|a)\s+)(.{5,80}?)\s+(?:position|role|opening)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:re|regarding|about)[:\s]+(.{5,80}?)\s+(?:position|role|at\s)",
        re.IGNORECASE,
    ),
    re.compile(
        r"application (?:for|to)\s+(.{5,80}?)(?:\s+at\s|\s*$|\s*[.\n])",
        re.IGNORECASE,
    ),
]


class EmailParser:
    """Parse common job-related email formats and extract structured data."""

    def parse(self, sender: str, subject: str, body: str) -> ParsedEmail | None:
        combined = f"{subject} {body}"
        combined_lower = combined.lower()
        ats_source = self._detect_ats(sender)
        company = self._extract_company(sender, combined)
        job_title = self._extract_job_title(subject, body)
        dates = self._extract_dates(body)

        # Check patterns in priority order
        for action, patterns, base_confidence in [
            ("offer", _OFFER_PATTERNS, 0.90),
            ("interview", _INTERVIEW_PATTERNS, 0.80),
            ("rejection", _REJECTION_PATTERNS, 0.85),
            ("outreach", _OUTREACH_PATTERNS, 0.70),
        ]:
            for pattern in patterns:
                if re.search(pattern, combined_lower):
                    confidence = base_confidence
                    # Boost confidence if from a known ATS
                    if ats_source:
                        confidence = min(confidence + 0.05, 1.0)
                    return ParsedEmail(
                        action=action,
                        confidence=confidence,
                        company=company,
                        job_title=job_title,
                        dates=dates,
                        ats_source=ats_source,
                    )

        return None

    def _detect_ats(self, sender: str) -> str | None:
        sender_lower = sender.lower()
        for domain, ats in _ATS_DOMAINS.items():
            if domain in sender_lower:
                return ats
        return None

    def _extract_company(self, sender: str, combined_text: str) -> str | None:
        # Try sender domain first
        domain_match = re.search(r"@([\w.-]+)\.\w+", sender)
        if domain_match:
            domain = domain_match.group(1)
            # Skip generic email / ATS domains
            skip_domains = {
                "gmail", "yahoo", "outlook", "hotmail",
                "greenhouse", "greenhouse-mail", "lever",
                "icims", "myworkdayjobs", "myworkday",
                "noreply", "no-reply", "notifications",
            }
            if domain.lower() not in skip_domains:
                return domain.replace("-", " ").title()

        # Fallback: "at <Company>" pattern
        at_pat = r"\bat\s+([A-Z][\w\s&.-]{1,50}?)(?:\.|,|\s+for|\s+and|\s*$)"
        at_match = re.search(at_pat, combined_text, flags=re.IGNORECASE)
        if at_match:
            return at_match.group(1).strip()

        return None

    def _extract_job_title(self, subject: str, body: str) -> str | None:
        combined = f"{subject} {body}"
        for pattern in _TITLE_PATTERNS:
            m = pattern.search(combined)
            if m:
                title = m.group(1).strip()
                # Basic cleanup
                title = re.sub(r"\s+", " ", title)
                if len(title) > 5:
                    return title
        return None

    def _extract_dates(self, body: str) -> list[datetime]:
        results: list[datetime] = []
        for match in _DATE_PATTERN.finditer(body):
            parsed = self._try_parse_date(match.group(0))
            if parsed is not None:
                results.append(parsed)
        return results

    def _try_parse_date(self, text: str) -> datetime | None:
        text = text.strip().rstrip(",")

        # Try ISO format: 2026-03-25
        iso_match = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
        if iso_match:
            try:
                return datetime(
                    int(iso_match.group(1)),
                    int(iso_match.group(2)),
                    int(iso_match.group(3)),
                )
            except ValueError:
                return None

        # Try US format: 3/25/2026
        us_match = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", text)
        if us_match:
            try:
                year = int(us_match.group(3))
                if year < 100:
                    year += 2000
                return datetime(year, int(us_match.group(1)), int(us_match.group(2)))
            except ValueError:
                return None

        # Try "Month Day, Year" format
        # Strip leading day-of-week
        text = re.sub(
            r"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )
        month_match = re.match(
            r"([A-Za-z]+)\s+(\d{1,2})(?:,?\s+(\d{4}))?", text
        )
        if month_match:
            month_name = month_match.group(1).lower()
            month = _MONTH_MAP.get(month_name)
            if month is not None:
                day = int(month_match.group(2))
                year = int(month_match.group(3)) if month_match.group(3) else 2026
                try:
                    return datetime(year, month, day)
                except ValueError:
                    return None

        return None
