# Does JobRadar Need ML, NLP, Deep Learning, or AI Agents? An Honest Assessment

**Date: 2026-03-28 | Research basis: Web search + arXiv + training knowledge**

---

## Executive Summary

For a **single-user, local-first** job search app on 16GB RAM with no GPU:

| Technology | Verdict | Where It Helps | Where It's Overkill |
|-----------|---------|---------------|---------------------|
| Traditional ML | **MAYBE** | Outcome prediction (after 200+ apps) | Job matching (LLM is better) |
| NLP (spaCy etc.) | **NO** | LLMs have replaced these pipelines | Everything -- use LLMs instead |
| Deep Learning | **YES (embeddings only)** | Semantic search via sentence-transformers | Training custom models |
| AI Agents | **YES (deterministic hybrid)** | Auto-apply with scripted + AI fallback | Fully autonomous browser agents |
| LLM API calls | **YES** | Resume gen, cover letters, copilot, scoring | Simple lookups, CRUD ops |

---

## 1. Traditional ML

### Where It COULD Help

**Job-Profile Match Scoring (MAYBE)**

- LLMs (Claude Haiku, GPT-4o-mini) can score job-profile match on 0-1 scale via prompting
- Traditional ML (XGBoost, LightGBM) needs training data to beat this
- With <50 applications: **LLM wins** (zero training data needed)
- With 200+ applications with tracked outcomes: ML *might* outperform because it learns YOUR specific patterns
- **Recommendation**: Start with LLM scoring. After 200+ tracked applications, train a simple XGBoost model and A/B test against LLM

**Application Outcome Prediction (MAYBE after 200+ apps)**

- HistGradientBoosting (scikit-learn) can predict interview likelihood from features: company size, role seniority, resume match score, application method, time-to-apply
- Cold start problem is real: need 200+ labeled outcomes for meaningful signal
- **Recommendation**: Don't build this upfront. Track outcomes in DB. After 200+ apps, run a retrospective analysis to see if a model adds value.

**Deduplication: Splink vs SimHash (NO -- current approach is fine)**

- Splink uses Fellegi-Sunter probabilistic linkage, deduplicates 7M records in 2 minutes
- But JobRadar has ATS composite keys (`ats_job_id + ats_provider`) which are deterministic
- SimHash catches near-duplicates across different sources
- **The combination of ATS composite key + SimHash already covers >95% of dedup cases**
- Splink adds complexity (DuckDB backend, training parameters) for marginal improvement
- **Recommendation**: Keep current SimHash + ATS key approach. Not worth adding Splink.

### Where Traditional ML is OVERKILL

- **Job matching with small data**: LLMs have "inherent world knowledge" that minimizes dependency on training data. A 2025 study showed LLMs matched 10 user profiles to 1,000 jobs effectively with zero training data.
- **Resume optimization**: No meaningful training signal until you have hundreds of tracked outcomes
- **Salary prediction**: External data sources (BLS, Glassdoor) are more reliable than a model trained on your limited data

Sources:
- [Generative Job Recommendations with LLM (arXiv 2307.02157)](https://arxiv.org/pdf/2307.02157)
- [Human and LLM-Based Resume Matching (ACL 2025)](https://aclanthology.org/2025.findings-naacl.270.pdf)
- [RAG-Enhanced LLM Job Recommendation (IJERT)](https://www.ijert.org/rag-enhanced-llm-job-recommendation-systems-balancing-efficiency-and-accuracy-in-candidate-job-matching)
- [Eugene Yan: Improving RecSys with LLMs](https://eugeneyan.com/writing/recsys-llm/)
- [Splink GitHub](https://github.com/moj-analytical-services/splink)

---

## 2. NLP (spaCy, NLTK, etc.)

### The Honest Truth: LLMs Have Replaced These Pipelines

| NLP Task | Traditional NLP | LLM Approach | Winner |
|----------|----------------|-------------|--------|
| Resume parsing (NER) | spaCy custom model, needs labeled data | Claude Haiku structured extraction | **LLM** (zero training, better accuracy) |
| Skill extraction from JD | spaCy NER + pattern matching | GPT-4o-mini with schema | **LLM** (handles variations) |
| Sentiment analysis | VADER, TextBlob | Not needed for job search | N/A |
| Text classification | scikit-learn + TF-IDF | LLM with prompt | **LLM** (zero training) |
| Keyword extraction | TF-IDF, RAKE, YAKE | LLM extraction | **Tie** (TF-IDF is free + fast) |

### What to Keep from NLP

- **TF-IDF for keyword extraction**: Free, fast, no API cost. Good for ATS keyword scoring.
- **Fuzzy matching (RapidFuzz)**: Jaro-Winkler for form field matching, question dedup. Not an LLM task.
- **Text normalization**: Lowercasing, stripping, company name normalization. Simple string ops.

### What to NOT Build

- Don't train a spaCy NER model for resume parsing. Claude Haiku does it better at ~$0.001 per resume.
- Don't build a text classification pipeline. LLM prompting handles classification trivially.
- Don't invest in NLTK/spaCy dependency overhead when LLM APIs exist.

### Cost Comparison

| Task | spaCy (local, free) | Claude Haiku (~$0.001/call) |
|------|--------------------|-----------------------------|
| Resume parsing | Requires labeled training data + model maintenance | Zero-shot, immediate |
| Skill extraction | Custom patterns + NER | Zero-shot, handles edge cases |
| Setup time | Days-weeks | Minutes (write prompt) |
| Accuracy | 85-90% (trained) | 90-95% (zero-shot) |
| Running cost | $0 | ~$0.50/day at 500 calls |

**Verdict**: For a single-user app, the $0.50/day for LLM beats days of NLP model training.

---

## 3. Deep Learning

### YES: Embeddings for Semantic Search

This is the ONE deep learning component that is genuinely needed:

- **nomic-embed-text-v1.5**: Surpasses OpenAI text-embedding-ada-002 and text-embedding-3-small
- **nomic-embed-text-v2**: Apache 2.0, MoE architecture, multilingual
- **Local via Ollama**: Complete privacy, no API cost, runs on CPU
- **Cost comparison**: OpenAI embeddings = $0.02-0.13/M tokens. Local = $0.
- **Memory**: nomic-embed-text ~500MB model + ~200MB ONNX runtime = ~700MB on 16GB RAM

**Use cases in JobRadar:**
1. Job description semantic search (already implemented via pgvector)
2. Resume-to-JD similarity scoring
3. Near-duplicate detection (embedding cosine > threshold)
4. RAG retrieval for successful resume examples

### NO: Training Custom Deep Learning Models

- **No GPU**: Training on CPU is 10-100x slower
- **Single user**: Not enough data to fine-tune meaningfully
- **ONNX inference on CPU**: Works for pre-trained models (embeddings), not for training
- **Don't fine-tune**: Use pre-trained embedding models as-is. They're good enough.

Sources:
- [Nomic Embed Text V1 Blog](https://www.nomic.ai/blog/posts/nomic-embed-text-v1)
- [Top Embedding Models 2025](https://artsmart.ai/blog/top-embedding-models-in-2025/)
- [Best Embedding Models 2026](https://elephas.app/blog/best-embedding-models)
- [BentoML Open-Source Embeddings 2026](https://www.bentoml.com/blog/a-guide-to-open-source-embedding-models)

---

## 4. AI Agents and Agentic Workflows

### The State of Browser Agents (2025-2026)

**Browser-Use** (78K GitHub stars):
- Success rate: **89%** (11% failure rate)
- Not acceptable for critical workflows (job applications)

**OpenAI Operator**: Launched January 2025, **discontinued August 2025** -- couldn't achieve production reliability.

**Failure patterns**:
- Vision models struggle with date pickers, dropdowns, dynamic forms
- Navigation loops on unexpected page elements
- 6.7 second inference latency per action (too slow for multi-step forms)

### The Right Approach: Deterministic Hybrid

**2025-2026 consensus**: Production systems use a **blended model**:
- **Deterministic scripts** for known ATS forms (Greenhouse, Lever, Workday) -- 100% reliable
- **AI fallback** for unknown/custom forms only
- **Human-in-the-loop** for CAPTCHA and review before submit

**This is exactly what JobRadar already has**: dedicated adapters per ATS with scripted form filling, plus `question_engine.py` for LLM-powered unknown question answering.

### Where Agents DO Help

| Workflow | Agent Type | Reliability |
|----------|-----------|-------------|
| Auto-apply to known ATS | Scripted adapter (not an agent) | ~99% |
| Auto-apply to unknown form | Browser agent (browser-use) | ~89% |
| Company research for interview prep | Multi-step LLM + web search | ~95% |
| Resume tailoring | Single LLM call (not an agent) | ~98% |
| Offer evaluation (LLM council) | Multi-model ensemble | ~95% |
| Email monitoring + status update | Rule-based + LLM classifier | ~97% |

### Where Agents are OVERKILL

- **Job listing extraction**: Use CSS selectors or API calls, not an agent
- **Pipeline management**: CRUD operations, not agentic
- **Simple Q&A (copilot)**: Single LLM call, not a multi-step agent
- **Resume PDF generation**: Template rendering, not an agent task

### LLM Council / Ensemble

For high-stakes decisions (offer evaluation, career pivots):
- Query 2-3 different models (Claude Haiku + GPT-4o-mini + local Ollama)
- Compare responses for consensus
- Flag disagreements for human review
- Cost: ~$0.01-0.03 per council session

Sources:
- [Browserless: State of AI Browser Automation 2026](https://www.browserless.io/blog/state-of-ai-browser-automation-2026)
- [arXiv: Building Browser Agents](https://arxiv.org/html/2511.19477v1)
- [FillApp: State of AI Browser Agents 2025](https://fillapp.ai/blog/the-state-of-ai-browser-agents-2025)
- [Skyvern: AI Web Agents Guide](https://www.skyvern.com/blog/ai-web-agents-complete-guide-to-intelligent-browser-automation-november-2025/)
- [InfoWorld: When will browser agents do real work?](https://www.infoworld.com/article/4081396/when-will-browser-agents-do-real-work.html)

---

## 5. Practical Recommendation Framework

For each JobRadar capability, the RIGHT level of AI:

| Capability | Right Level | Tool | Cost/Call |
|-----------|------------|------|-----------|
| Job scraping | **Rule-based** | httpx + CSS selectors | $0 |
| ATS detection | **Rule-based** | URL patterns + HTML signals | $0 |
| Job dedup | **Rule + embedding** | ATS key + SimHash + cosine sim | $0 |
| Job-profile scoring | **LLM API** | Claude Haiku | ~$0.001 |
| Semantic search | **Embedding** | nomic-embed + pgvector | $0 (local) |
| Resume tailoring | **LLM API + guardrails** | Claude Haiku + Guardrails AI | ~$0.002 |
| Cover letter gen | **LLM API** | Claude Haiku | ~$0.002 |
| Interview prep | **LLM API** | Claude Haiku / GPT-4o | ~$0.005 |
| Auto-apply (known ATS) | **Scripted adapter** | Playwright + adapter | $0 |
| Auto-apply (unknown) | **Hybrid agent** | Script + browser-use fallback | ~$0.05 |
| Form question answering | **LLM API + RAG** | Retrieve past answers + LLM | ~$0.002 |
| Email status detection | **Rule + LLM** | Regex patterns + LLM classifier | ~$0.001 |
| Salary research | **LLM API** | Claude Haiku with web data | ~$0.003 |
| Offer evaluation | **LLM council** | 2-3 models + human review | ~$0.02 |
| Outcome prediction | **ML (after 200+ apps)** | XGBoost | $0 |
| Networking messages | **LLM API** | Claude Haiku | ~$0.002 |
| ATS keyword score | **TF-IDF** | scikit-learn TfidfVectorizer | $0 |
| Ghost job detection | **Rule-based** | Posting age + repost count + signals | $0 |

### Daily AI Cost Estimate (Active Job Search)

- 50 job scores: $0.05
- 5 resume tailorings: $0.01
- 3 cover letters: $0.006
- 2 interview preps: $0.01
- 10 copilot questions: $0.01
- 100 email classifications: $0.10
- 2 form question sessions: $0.004
- **Total: ~$0.19/day = ~$5.70/month**

This is trivially cheap. The LLM-first approach is economically viable for a single user.

---

## 6. What LinkedIn/Indeed Actually Do (For Context)

### LinkedIn (2025-2026)
- Uses BERT-based models for job-candidate matching
- Graph neural networks for relationship-aware recommendations
- Millions of training examples from user interactions
- **None of this is replicable at single-user scale**

### Indeed
- Ensemble of gradient boosted trees + neural networks
- Billions of data points from application/hire outcomes
- Real-time personalization based on browsing behavior
- **Again, irrelevant at single-user scale**

### The Takeaway

These companies use traditional ML because they have **billions of data points**. At single-user scale, LLMs with their pre-trained world knowledge are a better fit because they don't need training data.

---

## 7. Final Verdict

### Build This

1. **LLM API integration** (already exists) -- the right tool for 80% of AI tasks
2. **Local embeddings** (already exists) -- nomic-embed for semantic search, free
3. **Guardrails pipeline** (new) -- prevent fabrication in resume/cover letter gen
4. **Evaluation harness** (new) -- promptfoo for regression testing
5. **RAG learning loop** (new) -- retrieve successful past resumes as context

### Don't Build This

1. **Custom ML models** -- not enough data for a single user
2. **spaCy NLP pipelines** -- LLMs are better and cheaper at this scale
3. **Fine-tuned language models** -- no GPU, not enough data
4. **Fully autonomous browser agents** -- 89% success rate is unacceptable for job applications
5. **Splink dedup** -- overkill when ATS composite keys + SimHash work

### Build This Later (After 200+ Applications)

1. **Simple outcome prediction** -- XGBoost on tracked application features
2. **Resume version A/B analysis** -- which variants get more callbacks
3. **Application timing optimization** -- when to apply for best response rate
