from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import structlog

from app.scraping.normalization import CompanyNormalizer, TitleNormalizerStripped
from app.scraping.port import ScrapedJob

logger = structlog.get_logger()

TRACKING_PARAMS = frozenset(
    {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "ref", "trk"}
)

ATS_PROVIDERS = frozenset({"greenhouse", "lever", "ashby"})
GREENHOUSE_JOB_PATH_RE = re.compile(r"/jobs/(?P<job_id>\d+)(?:/|$)")


def compute_ats_composite_key(
    provider_scope: str | None,
    ats_provider: str | None,
    ats_job_id: str | None,
) -> str | None:
    """Compute a deterministic SHA-256 composite key for ATS-origin jobs."""
    if not ats_provider or not ats_job_id:
        return None

    scope = (provider_scope or "").strip().lower()
    provider = ats_provider.strip().lower()
    job_id = ats_job_id.strip()
    if not provider or not job_id:
        return None

    raw = f"{scope}|{provider}|{job_id}"
    return hashlib.sha256(raw.encode()).hexdigest()


def derive_ats_identity(job: ScrapedJob) -> dict[str, str | None]:
    """Best-effort ATS identity derived from the current scraper payload shape."""
    provider = _extract_ats_provider(job)
    job_id = _extract_ats_job_id(job, provider)
    provider_scope = _extract_provider_scope(job, provider)
    return {
        "ats_provider": provider,
        "ats_job_id": job_id,
        "ats_composite_key": compute_ats_composite_key(provider_scope, provider, job_id),
    }


def _extract_ats_provider(job: ScrapedJob) -> str | None:
    explicit_field = job.ats_provider
    if isinstance(explicit_field, str) and explicit_field.strip():
        return explicit_field.strip().lower()

    explicit = job.extra_data.get("ats_provider")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip().lower()

    source = job.source.strip().lower()
    if source in ATS_PROVIDERS:
        return source

    if not job.source_url:
        return None

    parsed = urlparse(job.source_url)
    host = (parsed.hostname or "").lower()
    if host == "greenhouse" or host.endswith(".greenhouse.com"):
        return "greenhouse"
    if host == "lever.co" or host.endswith(".lever.co"):
        return "lever"
    if host == "ashbyhq.com" or host.endswith(".ashbyhq.com"):
        return "ashby"
    return None


def _extract_ats_job_id(job: ScrapedJob, provider: str | None) -> str | None:
    explicit_field = job.ats_job_id
    if isinstance(explicit_field, str) and explicit_field.strip():
        return explicit_field.strip()

    explicit = job.extra_data.get("ats_job_id")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()

    if not provider or not job.source_url:
        return None

    parsed = urlparse(job.source_url)
    path_parts = [part for part in parsed.path.split("/") if part]
    if not path_parts:
        return None

    if provider == "greenhouse":
        match = GREENHOUSE_JOB_PATH_RE.search(parsed.path)
        return match.group("job_id") if match else None

    if provider in {"lever", "ashby"}:
        return path_parts[-1]

    return None


def _extract_provider_scope(job: ScrapedJob, provider: str | None) -> str | None:
    explicit = job.extra_data.get("ats_company_domain")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip().lower()

    if job.company_domain and job.company_domain.strip():
        return job.company_domain.strip().lower()

    if not provider or not job.source_url:
        return None

    parsed = urlparse(job.source_url)
    path_parts = [part for part in parsed.path.split("/") if part]
    if not path_parts:
        return None

    if provider == "greenhouse":
        if "jobs" in path_parts:
            jobs_index = path_parts.index("jobs")
            if jobs_index > 0:
                return path_parts[jobs_index - 1].lower()
        return path_parts[0].lower()

    if provider in {"lever", "ashby"}:
        return path_parts[0].lower()

    return None


class DeduplicationService:
    """3-layer deduplication: exact hash -> URL match -> fuzzy simhash."""

    def __init__(
        self,
        feedback_overrides: dict[tuple[str, str], bool] | None = None,
    ) -> None:
        # Feedback overrides are populated by the feedback pipeline and
        # consulted by higher-level orchestration during pair review.
        self._feedback_overrides = feedback_overrides or {}
        self._company_normalizer = CompanyNormalizer()
        self._title_normalizer = TitleNormalizerStripped()

    def deduplicate(self, jobs: list[ScrapedJob]) -> list[ScrapedJob]:
        seen_ats_keys: set[str] = set()
        seen_hashes: set[str] = set()
        seen_urls: set[str] = set()
        unique: list[ScrapedJob] = []
        simhashes: list[int] = []

        for job in jobs:
            ats_identity = derive_ats_identity(job)
            ats_composite_key = ats_identity["ats_composite_key"]
            if ats_composite_key:
                if ats_composite_key in seen_ats_keys:
                    continue
                seen_ats_keys.add(ats_composite_key)

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
        normalized_title = self._title_normalizer.normalize(job.title)
        normalized_company = self._company_normalizer.normalize(job.company_name)
        content = f"{normalized_title}|{normalized_company}"
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

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
            h = int(
                hashlib.md5(token.encode(), usedforsecurity=False).hexdigest(),
                16,
            ) & ((1 << 64) - 1)
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
