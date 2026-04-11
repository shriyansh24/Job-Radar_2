WITH bm25 AS (
    __BM25_BASE_QUERY__
    LIMIT :fetch_limit
),
semantic AS (
    SELECT id, ROW_NUMBER() OVER (
        ORDER BY embedding <=> CAST(:q_emb AS vector)
    ) AS rank
    FROM jobs
    WHERE user_id = :user_id
      AND is_active = true
      AND embedding IS NOT NULL
    LIMIT :fetch_limit
),
rrf AS (
    SELECT id, :bm25_w * (1.0 / (:k + rank)) AS score,
           rank AS src_rank, 'bm25' AS src
    FROM bm25
    UNION ALL
    SELECT id, :sem_w * (1.0 / (:k + rank)) AS score,
           rank AS src_rank, 'semantic' AS src
    FROM semantic
),
combined AS (
    SELECT id, SUM(score) AS rrf_score,
           MIN(CASE WHEN src = 'bm25' THEN src_rank END) AS bm25_rank,
           MIN(CASE WHEN src = 'semantic' THEN src_rank END) AS semantic_rank
    FROM rrf
    GROUP BY id
    ORDER BY rrf_score DESC
    LIMIT :limit OFFSET :offset
)
SELECT id, rrf_score, bm25_rank, semantic_rank
FROM combined
ORDER BY rrf_score DESC
