from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()


class TFIDFScorer:
    """TF-IDF scoring of jobs against user resume/profile.

    Uses scikit-learn (lazy-imported to avoid heavy startup cost).
    """

    def __init__(self) -> None:
        self._vectorizer = None

    @property
    def vectorizer(self) -> Any | None:
        if self._vectorizer is None:
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer

                self._vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
            except ImportError:
                logger.warning(
                    "scikit_learn_not_installed",
                    hint="pip install scikit-learn",
                )
                return None
        return self._vectorizer

    def score_jobs(self, resume_text: str, jobs: list[object]) -> list[tuple[str, float]]:
        """Score jobs against resume text. Returns list of (job_id, score).

        Jobs should have .id, .title, .company_name, .description_clean,
        .skills_required, .tech_stack attributes.
        """
        if self.vectorizer is None:
            return []

        try:
            from sklearn.metrics.pairwise import cosine_similarity
        except ImportError:
            return []

        corpus = [resume_text] + [self._job_to_text(job) for job in jobs]
        tfidf_matrix = self.vectorizer.fit_transform(corpus)

        resume_vec = tfidf_matrix[0]
        scores: list[tuple[str, float]] = []
        for i, job in enumerate(jobs):
            sim = cosine_similarity(resume_vec, tfidf_matrix[i + 1])[0][0]
            score = round(sim * 100, 1)
            score = max(10.0, min(99.0, score))
            scores.append((str(getattr(job, "id", "")), score))

        return sorted(scores, key=lambda x: x[1], reverse=True)

    @staticmethod
    def _job_to_text(job: object) -> str:
        parts = [
            getattr(job, "title", "") or "",
            getattr(job, "company_name", "") or "",
            getattr(job, "description_clean", "") or "",
        ]
        skills = getattr(job, "skills_required", None) or []
        if skills:
            parts.extend(skills)
        stack = getattr(job, "tech_stack", None) or []
        if stack:
            parts.extend(stack)
        return " ".join(parts)
