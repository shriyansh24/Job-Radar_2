# Resume & Cover Letter Pipeline — Technical Design

> Full research output from the resume agent. No separate maintained extended-architecture doc exists on this branch; treat this page as the current research slice for the resume pipeline.

## Existing Assets (~70% Reuse)

- 3-stage LLM tailoring pipeline (`backend/app/resume/service.py`) → upgrade to 4-stage
- Gap analyzer (`backend/app/resume/gap_analyzer.py`) → enhance with semantic similarity
- Cover letter templates with 4 styles (`backend/app/nlp/cover_letter_templates.py`)
- Application model already has `resume_version_id` + `cover_letter_id` FKs

## Architecture Overview

```
INGESTION → IR → TAILORING → RENDERING → STORAGE → LEARNING
 (multi-      (JSON      (4-stage      (PDF/HTML     (DB +        (outcome
  format)      Resume)    + LLM)        preview)      versions)    tracking)
```

## A. Multi-Format Ingestion

| Format | Library | Speed |
|--------|---------|-------|
| PDF | PyMuPDF4LLM | 120ms/5-page resume |
| DOCX | python-docx | 50ms |
| LaTeX (.tex) | pylatexenc + pandoc | 200ms |
| JSON Resume | Native parsing | <1ms |

All formats parse into a **structured IR** based on JSON Resume standard with ML-engineer extensions:
- Publications, patents, open-source contributions
- Per-role tech stack (not just a flat skills list)
- Metrics extraction ("improved latency by 40%")
- Section confidence scores from parser

## B. Rendering & Preview

| Target | Library | Where | Speed |
|--------|---------|-------|-------|
| PDF (server) | WeasyPrint (HTML/CSS→PDF) | Backend API | ~200ms/page |
| PDF (client preview) | @react-pdf/renderer | Frontend | Real-time |
| DOCX export | python-docx | Backend API | ~100ms |

Template system: Multiple resume templates user can switch between. Template-based editing with live preview (not WYSIWYG) — same approach as Reactive Resume.

## C. 4-Stage Tailoring Pipeline

```
Stage 1: ANALYZE — Parse JD, extract required/preferred skills, identify gaps
Stage 2: MATCH — Score resume sections against JD requirements (semantic similarity)
Stage 3: PROPOSE — LLM suggests bullet rewrites, skill reordering (USER REVIEWS HERE)
Stage 4: GENERATE — Apply approved changes, render final PDF
```

**Authenticity guard at Stage 3**: User reviews proposed changes before LLM rewrites. Never fabricate experience.

## D. Cover Letter Generation

- 4 tone styles: formal, conversational, technical, creative
- Company research integration (pull from company data in DB)
- Local LLM generation (Qwen3-8B via Ollama)
- Template variables: {company}, {role}, {why_excited}, {relevant_experience}

## E. Storage & Versioning

```
ResumeVersion table:
  - id, user_id, base_resume_id
  - job_id (null for base, set for tailored)
  - ir_json (structured intermediate representation)
  - rendered_pdf_path
  - embedding (vector(768) for similarity search)
  - tailoring_score (how much was changed from base)
  - created_at
```

## F. Learning Loop

- Track: which resume version → which application → which outcome
- Embed resume bullets + JD requirements → find which phrasings led to interviews
- RAG-powered suggestions: "This phrasing of X skill got callbacks at FAANG"
- Vector KB: LanceDB embedded (disk-based, no server) OR pgvector (already available)

## RAM Budget

| Component | RAM |
|-----------|-----|
| Ollama + Qwen3-8B | ~7GB |
| Embedding model (ONNX) | ~500MB |
| WeasyPrint rendering | ~200MB |
| Application code | ~200MB |
| **Total** | **~8GB** |
