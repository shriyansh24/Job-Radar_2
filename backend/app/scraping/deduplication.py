from __future__ import annotations

import hashlib
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import structlog

from app.scraping.port import ScrapedJob

logger = structlog.get_logger()

TRACKING_PARAMS = frozenset(
    {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "ref", "trk"}
)


class DeduplicationService:
    """3-layer deduplication: exact hash -> URL match -> fuzzy simhash."""

    def deduplicate(self, jobs: list[ScrapedJob]) -> list[ScrapedJob]:
        seen_hashes: set[str] = set()
        seen_urls: set[str] = set()
        unique: list[ScrapedJob] = []
        simhashes: list[int] = []

        for job in jobs:
            # Layer 1: Exact content hash
            content_hash = self._content_hash(job)
            if content_hash in seen_hashes:
                continue
            seen_hashes.add(content_hash)

            # Layer 2: URL dedup
            if job.source_url:
                normalized_url = self._normalize_url(job.source_url)
                if normalized_url in seen_urls:
                    continue
                seen_urls.add(normalized_url)

            # Layer 3: Simhash for near-duplicates
            simhash = self._compute_simhash(job)
            is_near_dup = False
            for existing_hash in simhashes:
                if self._hamming_distance(simhash, existing_hash) < 3:
                    is_near_dup = True
                    break
            if not is_near_dup:
                unique.append(job)
                simhashes.append(simhash)

        removed = len(jobs) - len(unique)
        if removed > 0:
            logger.info("dedup_complete", total=len(jobs), unique=len(unique), removed=removed)
        return unique

    def _content_hash(self, job: ScrapedJob) -> str:
        """MD5 of normalized title + company."""
        content = f"{job.title.lower().strip()}|{job.company_name.lower().strip()}"
        return hashlib.md5(content.encode()).hexdigest()

    def _normalize_url(self, url: str) -> str:
        """Remove tracking params, fragment; lowercase host."""
        parsed = urlparse(url)
        params = {k: v for k, v in parse_qs(parsed.query).items() if k not in TRACKING_PARAMS}
        return urlunparse(
            parsed._replace(
                netloc=parsed.netloc.lower(),
                query=urlencode(params, doseq=True),
                fragment="",
            )
        )

    def _compute_simhash(self, job: ScrapedJob) -> int:
        """64-bit simhash of title + company + first 500 chars of description."""
        text = f"{job.title} {job.company_name} {(job.description_raw or '')[:500]}"
        tokens = text.lower().split()
        v = [0] * 64
        for token in tokens:
            h = int(hashlib.md5(token.encode()).hexdigest(), 16) & ((1 << 64) - 1)
            for i in range(64):
                if h & (1 << i):
                    v[i] += 1
                else:
                    v[i] -= 1
        fingerprint = 0
        for i in range(64):
            if v[i] > 0:
                fingerprint |= 1 << i
        return fingerprint

    def _hamming_distance(self, a: int, b: int) -> int:
        """Count differing bits between two integers."""
        return bin(a ^ b).count("1")
