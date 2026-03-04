import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Job
from backend.schemas import JobBase, SemanticSearchResult
from backend.enrichment.embedding import embed_text, get_resume_embedding, embed_texts

import numpy as np

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/semantic", response_model=list[SemanticSearchResult])
async def semantic_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query_embedding = embed_text(q)

    # Fetch jobs with descriptions
    result = await db.execute(
        select(Job)
        .where(Job.description_clean.isnot(None))
        .where(Job.description_clean != "")
        .where(Job.duplicate_of.is_(None))
        .limit(500)
    )
    jobs = result.scalars().all()

    if not jobs:
        return []

    # Embed all job texts
    texts = []
    for job in jobs:
        skills = " ".join(job.skills_required or [])
        text = f"{job.title}. {skills}. {(job.description_clean or '')[:500]}"
        texts.append(text)

    job_embeddings = embed_texts(texts)
    similarities = np.dot(job_embeddings, query_embedding)

    # Sort by similarity
    indexed = list(enumerate(similarities))
    indexed.sort(key=lambda x: x[1], reverse=True)

    results = []
    for idx, sim in indexed[:limit]:
        results.append(
            SemanticSearchResult(
                job=JobBase.model_validate(jobs[idx]),
                similarity=round(float(sim), 4),
            )
        )

    return results
