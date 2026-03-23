"""Personal RAG pipeline. No LangChain. Vanilla Python + pgvector + LLM."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.enrichment.embedding import EmbeddingService
from app.enrichment.llm_client import LLMClient

logger = structlog.get_logger()

RAG_SYSTEM_PROMPT = (
    "You are a career coach analyzing a job seeker's personal application history. "
    "Be specific, reference actual companies and roles from the data provided, "
    "and give actionable advice. If the data is insufficient, say so honestly."
)

_JOBS_QUERY = text("""
    SELECT j.title, j.company_name, j.summary_ai,
           a.status, a.salary_offered, a.notes,
           1 - (j.embedding <=> :q_emb::vector) AS similarity
    FROM applications a
    JOIN jobs j ON a.job_id = j.id
    WHERE a.user_id = :uid AND j.embedding IS NOT NULL
    ORDER BY j.embedding <=> :q_emb::vector
    LIMIT 5
""")

_RESUMES_QUERY = text("""
    SELECT rv.label, rv.filename, rv.parsed_text
    FROM resume_versions rv
    WHERE rv.user_id = :uid AND rv.parsed_text IS NOT NULL
    ORDER BY rv.is_default DESC, rv.created_at DESC
    LIMIT 2
""")


class PersonalRAG:
    """Minimal RAG over a user's jobs, applications, and resumes."""

    def __init__(
        self, db: AsyncSession, embedder: EmbeddingService, llm: LLMClient
    ) -> None:
        self.db = db
        self.embedder = embedder
        self.llm = llm

    async def get_contexts(
        self, question_embedding: list[float], user_id: uuid.UUID
    ) -> list[str]:
        """Retrieve relevant context strings via pgvector similarity."""
        contexts: list[str] = []
        params = {"q_emb": str(question_embedding), "uid": str(user_id)}

        # Application history with job details
        try:
            rows = await self.db.execute(_JOBS_QUERY, params)
            for row in rows:
                r = row._mapping
                line = f"Applied to {r['title']} at {r['company_name']} -> {r['status']}"
                if r.get("salary_offered"):
                    line += f" (offered: ${r['salary_offered']:,.0f})"
                if r.get("notes"):
                    line += f" — {r['notes'][:200]}"
                contexts.append(line)
        except Exception as exc:
            logger.warning("rag_jobs_query_failed", error=str(exc))

        # Resume snippets
        try:
            rows = await self.db.execute(_RESUMES_QUERY, params)
            for row in rows:
                r = row._mapping
                name = r.get("label") or r.get("filename") or "resume"
                parsed = (r.get("parsed_text") or "")[:500]
                if parsed:
                    contexts.append(f"Resume '{name}': {parsed}")
        except Exception as exc:
            logger.warning("rag_resumes_query_failed", error=str(exc))

        return contexts

    async def query(self, question: str, user_id: uuid.UUID) -> str:
        """Full RAG flow: embed -> retrieve -> generate."""
        # 1. Embed the question
        q_embedding = self.embedder.embed_text(question)
        if q_embedding is None:
            return "Embedding service is not available. Cannot process your question."

        # 2. Retrieve contexts
        contexts = await self.get_contexts(q_embedding, user_id)
        if not contexts:
            return (
                "I don't have enough data about your application history yet. "
                "Apply to some jobs and check back!"
            )

        # 3. Build prompt and generate
        context_block = "\n---\n".join(contexts)
        prompt = (
            f"Based on this personal application data:\n{context_block}\n\n"
            f"Answer this question: {question}"
        )

        try:
            return await self.llm.chat(
                messages=[
                    {"role": "system", "content": RAG_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=2000,
            )
        except Exception as exc:
            logger.error("rag_llm_failed", error=str(exc))
            return f"Sorry, I encountered an error generating your answer: {exc}"
