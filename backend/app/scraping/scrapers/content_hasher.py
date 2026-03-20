"""Content-hash deduplication for scraped HTML pages.

Strips dynamic noise (timestamps, ads, session tokens) from raw HTML before
hashing, so cosmetic refreshes don't trigger re-processing of unchanged listings.
"""

from __future__ import annotations

import hashlib
import re

import structlog
from bs4 import BeautifulSoup

logger = structlog.get_logger()

_TS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?"),
    re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"),
    re.compile(r"\d{1,2}/\d{1,2}/\d{2,4} \d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?", re.IGNORECASE),
    re.compile(r"\d+ (?:second|minute|hour|day|week|month|year)s? ago", re.IGNORECASE),
    re.compile(r"(?:just now|today|yesterday)", re.IGNORECASE),
]

_NONCE_PATTERN = re.compile(r"\b[0-9a-f]{16,}\b", re.IGNORECASE)

_SESSION_PARAMS = re.compile(
    r'(?:sessionid|sid|token|nonce|_ga|utm_[a-z]+|ref|cb)=[^&"\s]+',
    re.IGNORECASE,
)

_DYNAMIC_TAGS = ("script", "style", "noscript", "iframe")

_AD_ATTRS = re.compile(
    r"(?:ad[-_]?|advertisement|tracking|analytics|banner|sponsor|promo)",
    re.IGNORECASE,
)


class ContentHasher:
    """Compute stable SHA-256 hashes of scraped HTML pages.

    The hash is computed over a canonicalised version of the page that has
    dynamic noise removed, so only genuine content changes cause the hash to differ.
    """

    def hash_page(self, html: str) -> str:
        """Return the SHA-256 hex digest of the cleaned HTML content."""
        if not html:
            return hashlib.sha256(b"").hexdigest()
        cleaned = self._clean_html(html)
        return hashlib.sha256(cleaned.encode("utf-8", errors="replace")).hexdigest()

    def _clean_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        for tag_name in _DYNAMIC_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        for tag in soup.find_all(True):
            tag_id = tag.get("id", "") or ""
            tag_classes = " ".join(tag.get("class") or [])
            if _AD_ATTRS.search(tag_id) or _AD_ATTRS.search(tag_classes):
                tag.decompose()

        text = soup.get_text(separator=" ")

        for pattern in _TS_PATTERNS:
            text = pattern.sub("", text)

        text = _NONCE_PATTERN.sub("", text)
        text = _SESSION_PARAMS.sub("", text)
        text = " ".join(text.split())

        return text
