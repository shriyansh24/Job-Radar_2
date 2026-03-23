from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from itertools import combinations
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import structlog
from rapidfuzz import fuzz

from app.scraping.normalization import CompanyNormalizer, LocationNormalizer, TitleNormalizer
from app.scraping.port import ScrapedJob

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.enrichment.embedding import EmbeddingService

logger = structlog.get_logger()

TRACKING_PARAMS = frozenset(
    {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "ref", "trk"}
)

# ── Thresholds ──────────────────────────────────────────────────────────
TITLE_SIMILARITY_THRESHOLD = 70  # Stage 2: RapidFuzz token_sort_ratio
EMBEDDING_COSINE_THRESHOLD = 0.92  # Stage 3: cosine similarity
LOCATION_SIMILARITY_THRESHOLD = 70  # Stage 4: location fuzzy match


def _compute_ats_key(
    company_domain: str | None,
    ats_provider: str | None,
    ats_job_id: str | None,
) -> str | None:
    """Compute a deterministic SHA-256 composite key for ATS-based dedup."""
    if not all([company_domain, ats_provider, ats_job_id]):
        return None
    domain = company_domain.lower().strip()  # type: ignore[union-attr]
    provider = ats_provider.lower()  # type: ignore[union-attr]
    job_id = ats_job_id.strip()  # type: ignore[union-attr]
    raw = f"{domain}|{provider}|{job_id}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ── Result dataclasses ──────────────────────────────────────────────────
@dataclass
class DedupDecision:
    """A single deduplication decision with confidence."""

    job_a: ScrapedJob
    job_b: ScrapedJob
    is_duplicate: bool
    confidence: float  # 0.0 - 1.0
    stage_decided: int  # which stage made the final call
    reason: str = ""


@dataclass
class DeduplicationResult:
    """Output of the 6-stage dedup pipeline."""

    unique_jobs: list[ScrapedJob] = field(default_factory=list)
    duplicate_pairs: list[DedupDecision] = field(default_factory=list)
    updated_jobs: list[tuple[str, ScrapedJob]] = field(default_factory=list)
    merged_groups: list[list[ScrapedJob]] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)


@dataclass
class CompanyBlock:
    """Jobs grouped by normalized company name."""

    company_key: str
    jobs: list[ScrapedJob] = field(default_factory=list)

    def add(self, job: ScrapedJob) -> None:
        self.jobs.append(job)

    def all_pairs(self) -> list[tuple[int, int]]:
        """Return all (i, j) index pairs within this block."""
        return list(combinations(range(len(self.jobs)), 2))


# ── 6-Stage Pipeline ───────────────────────────────────────────────────
class SixStageDeduplicator:
    """6-stage deduplication pipeline.

    Stage 1: ATS composite key exact match
    Stage 2: RapidFuzz title fast-reject within company blocks
    Stage 3: Embedding cosine similarity within surviving pairs
    Stage 4: Location/department disambiguation
    Stage 5: Merge to canonical (group formation)
    Stage 6: Confidence scoring for each decision
    """

    def __init__(
        self,
        db: AsyncSession | None = None,
        embedding_service: EmbeddingService | None = None,
        company_normalizer: CompanyNormalizer | None = None,
        title_normalizer: TitleNormalizer | None = None,
        location_normalizer: LocationNormalizer | None = None,
    ) -> None:
        self.db = db
        self.embedder = embedding_service
        self.co_norm = company_normalizer or CompanyNormalizer()
        self.title_norm = title_normalizer or TitleNormalizer()
        self.loc_norm = location_normalizer or LocationNormalizer()

    async def deduplicate(self, incoming: list[ScrapedJob]) -> DeduplicationResult:
        """Run all 6 stages and return structured results."""
        result = DeduplicationResult()
        if not incoming:
            return result

        # ── Stage 1: ATS composite key exact match ──────────────────
        candidates: list[ScrapedJob] = []
        ats_seen: dict[str, ScrapedJob] = {}

        for job in incoming:
            composite_key = _compute_ats_key(
                job.company_domain, job.ats_provider, job.ats_job_id
            )
            if composite_key:
                if composite_key in ats_seen:
                    decision = DedupDecision(
                        job_a=ats_seen[composite_key],
                        job_b=job,
                        is_duplicate=True,
                        confidence=1.0,
                        stage_decided=1,
                        reason="ats_composite_key_match",
                    )
                    result.duplicate_pairs.append(decision)
                    result.stats["stage1_ats_dupes"] = (
                        result.stats.get("stage1_ats_dupes", 0) + 1
                    )
                    continue
                ats_seen[composite_key] = job

            # Also check DB if we have a session
            if composite_key and self.db:
                existing_id = await self._lookup_composite_key_in_db(composite_key)
                if existing_id:
                    result.updated_jobs.append((existing_id, job))
                    result.stats["stage1_db_updates"] = (
                        result.stats.get("stage1_db_updates", 0) + 1
                    )
                    continue

            candidates.append(job)

        # ── Stage 2+: Block by company, then run pair stages ────────
        blocks = self._block_by_company(candidates)
        duplicate_ids: set[int] = set()  # set of id(job) for duplicates

        for block in blocks:
            if len(block.jobs) < 2:
                continue

            pairs = block.all_pairs()
            candidate_pairs: list[tuple[int, int, float]] = []

            # ── Stage 2: RapidFuzz title fast-reject ────────────────
            for i, j in pairs:
                norm_title_a = self.title_norm.normalize(block.jobs[i].title)
                norm_title_b = self.title_norm.normalize(block.jobs[j].title)
                title_sim = fuzz.token_sort_ratio(norm_title_a, norm_title_b)
                if title_sim >= TITLE_SIMILARITY_THRESHOLD:
                    candidate_pairs.append((i, j, title_sim))

            result.stats["stage2_title_passed"] = (
                result.stats.get("stage2_title_passed", 0) + len(candidate_pairs)
            )
            result.stats["stage2_title_rejected"] = (
                result.stats.get("stage2_title_rejected", 0)
                + len(pairs)
                - len(candidate_pairs)
            )

            if not candidate_pairs:
                continue

            # ── Stage 3: Embedding cosine within surviving pairs ────
            embeddings: dict[int, list[float]] = {}
            if self.embedder:
                for i, j, _ in candidate_pairs:
                    for idx in (i, j):
                        if idx not in embeddings:
                            text = self._build_embed_text(block.jobs[idx])
                            emb = self.embedder.embed_text(text)
                            if emb:
                                embeddings[idx] = emb

            cosine_pairs: list[tuple[int, int, float, float]] = []
            for i, j, title_sim in candidate_pairs:
                if i in embeddings and j in embeddings:
                    cos_sim = self._cosine_similarity(embeddings[i], embeddings[j])
                    if cos_sim >= EMBEDDING_COSINE_THRESHOLD:
                        cosine_pairs.append((i, j, title_sim, cos_sim))
                else:
                    # No embeddings available: fall back to title-only with
                    # a higher threshold to compensate
                    if title_sim >= 90:
                        cosine_pairs.append((i, j, title_sim, 0.0))

            result.stats["stage3_embedding_passed"] = (
                result.stats.get("stage3_embedding_passed", 0) + len(cosine_pairs)
            )

            # ── Stage 4: Location/department disambiguation ─────────
            confirmed_pairs: list[tuple[int, int, float, float]] = []
            for i, j, title_sim, cos_sim in cosine_pairs:
                if self._different_department_or_location(block.jobs[i], block.jobs[j]):
                    result.stats["stage4_disambiguated"] = (
                        result.stats.get("stage4_disambiguated", 0) + 1
                    )
                    decision = DedupDecision(
                        job_a=block.jobs[i],
                        job_b=block.jobs[j],
                        is_duplicate=False,
                        confidence=0.0,
                        stage_decided=4,
                        reason="location_or_department_differs",
                    )
                    result.duplicate_pairs.append(decision)
                    continue
                confirmed_pairs.append((i, j, title_sim, cos_sim))

            # ── Stage 5 & 6: Group duplicates and score ─────────────
            # Use union-find by object identity to build merge groups
            block_parent: dict[int, int] = {}  # id(job) -> id(root job)
            for i, j, title_sim, cos_sim in confirmed_pairs:
                confidence = self._compute_confidence(title_sim, cos_sim)
                job_a = block.jobs[i]
                job_b = block.jobs[j]
                decision = DedupDecision(
                    job_a=job_a,
                    job_b=job_b,
                    is_duplicate=True,
                    confidence=confidence,
                    stage_decided=5,
                    reason="confirmed_duplicate",
                )
                result.duplicate_pairs.append(decision)
                # Mark the second job as a duplicate
                duplicate_ids.add(id(job_b))
                # Union-find: link j's root to i's root
                id_a = id(job_a)
                id_b = id(job_b)
                root_a = id_a
                while block_parent.get(root_a, root_a) != root_a:
                    root_a = block_parent[root_a]
                root_b = id_b
                while block_parent.get(root_b, root_b) != root_b:
                    root_b = block_parent[root_b]
                if root_a != root_b:
                    block_parent[root_b] = root_a

            # Collect merge groups from union-find
            if block_parent:
                groups: dict[int, list[ScrapedJob]] = {}
                all_ids_in_uf = set(block_parent.keys()) | set(block_parent.values())
                for job in block.jobs:
                    jid = id(job)
                    if jid not in all_ids_in_uf:
                        continue
                    root = jid
                    while block_parent.get(root, root) != root:
                        root = block_parent[root]
                    groups.setdefault(root, []).append(job)
                for group in groups.values():
                    if len(group) > 1:
                        result.merged_groups.append(group)

        # Collect unique jobs (not marked as duplicates)
        for job in candidates:
            if id(job) not in duplicate_ids:
                result.unique_jobs.append(job)

        result.stats["total_input"] = len(incoming)
        result.stats["total_unique"] = len(result.unique_jobs)
        result.stats["total_duplicates"] = len(duplicate_ids)
        result.stats["total_updated"] = len(result.updated_jobs)
        result.stats["merge_groups"] = len(result.merged_groups)

        if duplicate_ids or result.updated_jobs:
            logger.info(
                "six_stage_dedup_complete",
                **result.stats,
            )

        return result

    def _block_by_company(self, jobs: list[ScrapedJob]) -> list[CompanyBlock]:
        """Group jobs by normalized company name."""
        blocks: dict[str, CompanyBlock] = {}
        for job in jobs:
            key = self.co_norm.normalize(job.company_name)
            if not key:
                key = "__unknown__"
            blocks.setdefault(key, CompanyBlock(company_key=key))
            blocks[key].add(job)
        return list(blocks.values())

    def _different_department_or_location(self, a: ScrapedJob, b: ScrapedJob) -> bool:
        """Check if two jobs differ significantly in location or department."""
        # Department check
        dept_a = (a.extra_data or {}).get("department", "")
        dept_b = (b.extra_data or {}).get("department", "")
        if dept_a and dept_b and dept_a.lower().strip() != dept_b.lower().strip():
            return True

        # Location check
        loc_a = self.loc_norm.normalize(a.location)
        loc_b = self.loc_norm.normalize(b.location)
        if loc_a and loc_b:
            loc_sim = fuzz.ratio(loc_a, loc_b)
            if loc_sim < LOCATION_SIMILARITY_THRESHOLD:
                return True

        return False

    @staticmethod
    def _build_embed_text(job: ScrapedJob) -> str:
        """Build text for embedding from job fields."""
        parts = [job.title, job.company_name]
        if job.description_raw:
            parts.append(job.description_raw[:1000])
        return " ".join(parts)

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def _compute_confidence(title_sim: float, cos_sim: float) -> float:
        """Stage 6: Compute confidence score (0-1) for a dedup decision.

        Weights: title similarity 40%, embedding cosine 60%.
        If no embedding is available (cos_sim == 0), use title only.
        """
        if cos_sim > 0:
            raw = 0.4 * (title_sim / 100.0) + 0.6 * cos_sim
        else:
            raw = title_sim / 100.0
        return round(min(max(raw, 0.0), 1.0), 4)

    async def _lookup_composite_key_in_db(self, composite_key: str) -> str | None:
        """Look up an ATS composite key in the jobs table. Returns job ID if found."""
        if not self.db:
            return None
        try:
            from sqlalchemy import select

            from app.jobs.models import Job

            stmt = select(Job.id).where(Job.ats_composite_key == composite_key).limit(1)
            row = await self.db.scalar(stmt)
            return row
        except Exception:
            return None

    def deduplicate_sync(self, jobs: list[ScrapedJob]) -> list[ScrapedJob]:
        """Synchronous convenience wrapper that runs the pipeline without DB stages.

        Returns just the unique jobs list (backward-compatible signature).
        """
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(self.deduplicate(jobs))
            return result.unique_jobs
        finally:
            loop.close()


# ── Legacy service (backward compatible) ────────────────────────────────

class DeduplicationService:
    """3-layer deduplication: exact hash -> URL match -> fuzzy simhash.

    Retained for backward compatibility. New code should use
    SixStageDeduplicator for the full pipeline.
    """

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
        content = f"{job.title.lower().strip()}|{job.company_name.lower().strip()}"
        return hashlib.md5(content.encode()).hexdigest()

    def _normalize_url(self, url: str) -> str:
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
        return bin(a ^ b).count("1")
