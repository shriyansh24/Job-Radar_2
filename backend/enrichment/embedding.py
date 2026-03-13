import logging
import os
from typing import Optional

# Prevent transformers from trying to load TensorFlow (we only use PyTorch)
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")

import numpy as np
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import async_session
from backend.models import Job, UserProfile

logger = logging.getLogger(__name__)

_model = None
_resume_embedding: Optional[np.ndarray] = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Loaded sentence-transformers model: all-MiniLM-L6-v2")
    return _model


def embed_text(text: str) -> np.ndarray:
    model = _get_model()
    return model.encode(text, normalize_embeddings=True)


def embed_texts(texts: list[str]) -> np.ndarray:
    model = _get_model()
    return model.encode(texts, normalize_embeddings=True, batch_size=32)


async def load_resume_embedding():
    global _resume_embedding
    async with async_session() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.id == 1)
        )
        profile = result.scalar_one_or_none()
        if profile and profile.resume_text:
            _resume_embedding = embed_text(profile.resume_text)
            logger.info("Resume embedding loaded/updated")
        else:
            _resume_embedding = None
            logger.info("No resume found, match scoring disabled")


def get_resume_embedding() -> Optional[np.ndarray]:
    return _resume_embedding


def compute_match_score(job_text: str) -> Optional[float]:
    if _resume_embedding is None:
        return None
    job_embedding = embed_text(job_text)
    similarity = float(np.dot(_resume_embedding, job_embedding))
    return round(max(0, min(100, similarity * 100)), 1)


async def score_jobs_batch():
    if _resume_embedding is None:
        logger.info("No resume embedding available, skipping match scoring")
        return

    async with async_session() as session:
        result = await session.execute(
            select(Job)
            .where(Job.match_score.is_(None))
            .where(Job.description_clean.isnot(None))
            .where(Job.description_clean != "")
            .limit(50)
        )
        jobs = result.scalars().all()

        if not jobs:
            return

        logger.info(f"Scoring {len(jobs)} jobs for resume match")

        texts = []
        job_ids = []
        for job in jobs:
            skills = " ".join(job.skills_required or [])
            text = f"{job.title}. {skills}. {(job.description_clean or '')[:500]}"
            texts.append(text)
            job_ids.append(job.job_id)

        embeddings = embed_texts(texts)
        scores = np.dot(embeddings, _resume_embedding)

        for job_id, score in zip(job_ids, scores):
            match_score = round(max(0, min(100, float(score) * 100)), 1)
            await session.execute(
                update(Job).where(Job.job_id == job_id).values(match_score=match_score)
            )

        await session.commit()
        logger.info(f"Match scoring complete for {len(jobs)} jobs")

    # Compute TF-IDF scores if NLP module available
    try:
        from backend.nlp.core import compute_tfidf_similarity
        if _resume_embedding is not None:
            async with async_session() as session:
                result = await session.execute(
                    select(Job)
                    .where(Job.tfidf_score.is_(None))
                    .where(Job.description_clean.isnot(None))
                    .limit(50)
                )
                tfidf_jobs = result.scalars().all()
                if tfidf_jobs:
                    profile_result = await session.execute(
                        select(UserProfile).where(UserProfile.id == 1)
                    )
                    profile = profile_result.scalar_one_or_none()
                    if profile and profile.resume_text:
                        for job in tfidf_jobs:
                            score = compute_tfidf_similarity(
                                profile.resume_text,
                                job.description_clean or ""
                            )
                            await session.execute(
                                update(Job).where(Job.job_id == job.job_id).values(tfidf_score=score)
                            )
                        await session.commit()
                        logger.info(f"TF-IDF scoring complete for {len(tfidf_jobs)} jobs")
    except ImportError:
        pass  # NLP module not available
    except Exception as e:
        logger.warning(f"TF-IDF scoring failed: {e}")
