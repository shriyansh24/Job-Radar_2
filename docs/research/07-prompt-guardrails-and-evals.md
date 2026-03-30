# Prompt Guardrails, Evaluation, and KB Learning for Resume/Cover Letter Generation

**Date: 2026-03-28 | Research basis: Web search + training knowledge**

---

## 1. Guardrail Frameworks

### Guardrails AI (guardrails-ai/guardrails)
- **GitHub**: ~15K stars, MIT license, Python
- **What it does**: Input/Output Guards that detect, quantify, and mitigate risks in LLM outputs
- **Guardrails Hub**: Collection of pre-built validators ("measures of specific types of risks")
- **Guardrails Index** (Feb 2025): First benchmark comparing 24 guardrails across 6 categories
- **Key for resumes**: Structured output validation (JSON schema enforcement), custom validators for factual consistency
- **Install**: `pip install guardrails-ai`

**Relevant validators for resume generation:**
- `ValidJson` / `ValidPydantic` -- ensure output matches schema
- `DetectPII` -- strip SSN, bank info, health info
- `ToxicLanguage` -- prevent unprofessional tone
- `ReadingTime` -- enforce length constraints
- Custom validators: compare output claims against user profile (no-fabrication)

### NVIDIA NeMo Guardrails
- **GitHub**: NVIDIA-NeMo/Guardrails, Apache 2.0
- **What it does**: Programmable guardrails for LLM conversational systems using Colang DSL
- **Hallucination detection**: Based on SelfCheckGPT -- samples multiple answers at high temperature, flags inconsistencies
- **Fact-checking**: ~80% accuracy on MS-MARCO; hallucination detection 95% with gpt-3.5-turbo
- **Cleanlab TLM integration**: State-of-the-art uncertainty estimation for real-time validation
- **Key for resumes**: Hallucination rail can catch fabricated skills/experience

### Comparison for JobRadar

| Feature | Guardrails AI | NeMo Guardrails |
|---------|--------------|-----------------|
| Resume-specific validators | Custom (write your own) | Custom (Colang flows) |
| Structured output enforcement | Native (Pydantic) | Via Colang actions |
| PII detection | Hub validator | Custom rail |
| Fabrication detection | Custom validator | SelfCheckGPT built-in |
| Ease of integration | Decorator/wrapper pattern | Colang config files |
| **Recommendation** | **Better fit** -- simpler, Pydantic-native | Better for chat/conversational systems |

Sources:
- [Guardrails AI GitHub](https://github.com/guardrails-ai/guardrails)
- [NeMo Guardrails GitHub](https://github.com/NVIDIA-NeMo/Guardrails)
- [CSA Guardrails Guide](https://cloudsecurityalliance.org/blog/2025/12/10/how-to-build-ai-prompt-guardrails-an-in-depth-guide-for-securing-enterprise-genai)
- [AI Agent Guardrails Production Guide 2026](https://authoritypartners.com/insights/ai-agent-guardrails-production-guide-for-2026/)
- [OpenLayer AI Guardrails Guide 2026](https://www.openlayer.com/blog/post/ai-guardrails-llm-guide)
- [Galileo 5 Best Guardrails Platforms 2026](https://galileo.ai/blog/best-ai-guardrails-platforms)

---

## 2. Specific Guardrail Patterns for Resume/Cover Letter

### No-Fabrication Guardrail (Critical)
**Problem**: LLM adds skills, experience, or credentials the user doesn't have.
**Solution**: Post-generation comparison pipeline:
1. Extract claims from generated resume (skills, job titles, companies, dates, certifications)
2. Compare each claim against user's master profile stored in DB
3. Flag any claim not found in profile as potential fabrication
4. Reject or highlight for user review

**Implementation**: Use an LLM-as-judge call with the user profile as context:
- System: "Compare the following resume claims against the user's verified profile. Flag any claim that is not supported by the profile."
- This is cheaper than it sounds -- Claude Haiku or GPT-4o-mini at ~$0.001 per check

### Tone Guardrail
**Problem**: LLM generates casual, AI-sounding, or inappropriate language.
**Signals to detect**: "Spearheaded" (overused), "synergy" (corporate fluff), slang, first-person inconsistency
**Solution**: Classifier (can be rule-based regex + small LLM check)

### PII Guardrail
**Problem**: SSN, bank details, health info leaking into LLM input/output.
**Solution**: Regex patterns for SSN, credit card, phone formats on both input and output. Guardrails AI `DetectPII` validator handles common patterns.

### ATS Keyword Guardrail
**Problem**: Generated resume doesn't include critical keywords from the job description.
**Solution**: Pre-generation: extract top-N keywords from JD via TF-IDF or LLM. Post-generation: check keyword presence. Score 0-100 based on coverage.

### Length Guardrail
**Problem**: Resume exceeds 1 page, cover letter exceeds 300 words.
**Solution**: Token count check post-generation. If over limit, re-generate with stricter prompt or truncate intelligently.

### Format Guardrail
**Problem**: Missing required sections (Education, Experience, Skills).
**Solution**: Pydantic schema validation -- resume must have all required sections before rendering to PDF/DOCX.

---

## 3. Evaluation Frameworks

### promptfoo
- **GitHub**: promptfoo/promptfoo, MIT license, 8K+ stars
- **Note**: As of March 2026, promptfoo joined OpenAI but remains open source
- **What it does**: CLI + library for evaluating LLM prompts against test cases with assertions
- **Key assertion types for resumes**:
  - `is-json` -- output is valid JSON
  - `contains` / `not-contains` -- keyword presence/absence
  - `llm-rubric` -- LLM judges output against criteria (most powerful for resume quality)
  - `javascript` -- custom JS assertion function
  - `python` -- custom Python assertion
  - `similar` -- semantic similarity check
  - `cost` -- assertion on API cost
  - `latency` -- assertion on response time
- **Golden test sets**: Define YAML test cases with input (job description + profile) and expected output criteria
- **CI integration**: `promptfoo eval --ci` for regression detection

### DeepEval
- **GitHub**: confident-ai/deepeval, Apache 2.0, 8K+ stars
- **What it does**: Pytest-inspired LLM evaluation framework
- **50+ built-in metrics** including Faithfulness, Contextual Relevancy, Answer Relevancy
- **Key for resumes**: Faithfulness metric (is the resume grounded in provided profile data?)
- **Advantage over promptfoo**: Native Python, pytest integration, more structured metrics

### RAGAS
- **Focus**: RAG evaluation specifically
- **Core metrics**: Faithfulness, Context Precision, Context Recall, Answer Relevancy
- **Key for resumes**: If using RAG to retrieve successful past resumes as context, RAGAS measures whether the generation is faithful to that context

### Recommended Eval Stack for JobRadar

**promptfoo for prompt regression testing** + **DeepEval for quality metrics**

| Eval Need | Tool | Why |
|-----------|------|-----|
| Prompt regression (did a prompt change break quality?) | promptfoo | CI-friendly, YAML config, fast |
| Faithfulness (no fabrication) | DeepEval | Built-in Faithfulness metric |
| Keyword coverage (ATS score) | Custom assertion in promptfoo | `python` assertion type |
| Tone/professionalism | `llm-rubric` in promptfoo | LLM judges tone on 1-5 scale |
| Format correctness | `is-json` + Pydantic | Schema validation |

### Cost of Evaluation

- **promptfoo with GPT-4o-mini**: ~$0.002 per test case (including LLM-rubric judge)
- **Full golden set (145 cases per doc spec)**: ~$0.30 per run
- **Daily sampled eval (20 cases)**: ~$0.04 per run
- **Monthly budget**: <$5

Sources:
- [promptfoo GitHub](https://github.com/promptfoo/promptfoo)
- [promptfoo Assertions Docs](https://www.promptfoo.dev/docs/configuration/expected-outputs/)
- [DeepEval GitHub](https://github.com/confident-ai/deepeval)
- [Helicone Eval Frameworks Comparison](https://www.helicone.ai/blog/prompt-evaluation-frameworks)
- [GoCodeo Top 5 Eval Frameworks 2025](https://www.gocodeo.com/post/top-5-ai-evaluation-frameworks-in-2025-from-ragas-to-deepeval-and-beyond)

---

## 4. Golden Test Sets for Resume/Cover Letter

### Resume Tailoring Test Set (20 cases)

Each case contains:
- **Input**: User profile (skills, experience, education) + Job description
- **Expected**: Tailored resume in structured format
- **Assertions**:
  1. `is-json` -- valid structured output
  2. `llm-rubric: "Resume emphasizes skills relevant to the job description"` (score >= 4/5)
  3. `llm-rubric: "No skills or experience are fabricated beyond what's in the user profile"` (score = 5/5)
  4. `llm-rubric: "Professional tone, no casual language or AI-sounding phrases"` (score >= 4/5)
  5. `python: assert_keyword_coverage(output, jd_keywords) >= 0.7` -- 70%+ JD keywords present
  6. `python: assert_word_count(output) <= 600` -- fits one page

### Cover Letter Test Set (20 cases)

Similar structure with additional assertions:
- Addresses specific company/role
- Under 300 words
- Includes call-to-action
- No generic filler ("I am writing to express my interest...")

### Form Question Answering Test Set (25 cases)

- Input: Question text + field type + user profile
- Assertions: Answer is relevant, concise, matches field constraints (char limit, dropdown options)

### Adversarial Test Set (30 cases)

- Prompts that try to get the LLM to fabricate credentials
- Prompts with adversarial job descriptions (unrealistic requirements)
- Edge cases: empty profile, profile with gaps, career changers

---

## 5. Learning from Knowledge Base

### The Feedback Loop Architecture

```
User Profile + JD --> Generate Resume --> User Reviews --> Submit Application
                                                              |
                                                              v
                                                    Outcome (interview/reject)
                                                              |
                                                              v
                                                    Store: resume_version + outcome
                                                              |
                                                              v
                                              RAG: retrieve successful resumes as few-shot examples
                                                              |
                                                              v
                                                    Improved next generation
```

### RAG for Resume Improvement

1. **Store**: Every submitted resume + its outcome (interview, rejection, ghosted) in `generated_resumes` table
2. **Embed**: Generate embedding of each resume using nomic-embed-text-v1.5
3. **Retrieve**: When generating a new resume, retrieve the 3 most similar previously-successful resumes (those that led to interviews)
4. **Augment**: Include successful resumes in the generation prompt as few-shot examples
5. **Generate**: LLM produces new resume informed by what worked before

### Outcome-Weighted Strategy

After 50+ applications with tracked outcomes:
- Calculate which resume sections, keywords, and styles correlate with positive outcomes
- Weight generation prompts toward successful patterns
- Surface insights: "Applications with quantified achievements get 2.3x more callbacks"

### Cold Start (Before Outcome Data Exists)

- Use general best practices from resume writing literature
- Use the user's strongest profile sections as emphasis targets
- After 10-20 applications, begin tracking and adjusting

### Question Answer Learning

From the completion program doc's `question_answers` table:
- Store every form question + approved answer + outcome
- Fuzzy-match new questions against stored answers (RapidFuzz, Jaro-Winkler >= 0.85)
- Pre-fill with stored answer if match found and previously approved
- Track `times_used` and `last_used_at` for staleness detection

Sources:
- [RAG-Enhanced LLM Job Recommendation (IJERT)](https://www.ijert.org/rag-enhanced-llm-job-recommendation-systems-balancing-efficiency-and-accuracy-in-candidate-job-matching)
- [Human and LLM-Based Resume Matching (ACL 2025)](https://aclanthology.org/2025.findings-naacl.270.pdf)
- [Improving RecSys with LLMs (Eugene Yan)](https://eugeneyan.com/writing/recsys-llm/)

---

## 6. Production Prompt Engineering for Resumes

### Temperature Settings
- **Resume bullet rewriting**: 0.2-0.3 (deterministic, factual)
- **Cover letter generation**: 0.4-0.6 (slightly creative, personalized)
- **Interview question generation**: 0.5-0.7 (creative variety)
- **Form question answering**: 0.1-0.2 (very deterministic)

### Few-Shot Examples
- Include 2-3 high-quality resume bullet transformations in the system prompt
- Example format: "Before: [generic bullet] -> After: [tailored, quantified bullet]"
- Rotate few-shot examples from the RAG retrieval of successful past resumes

### System Prompt Structure
1. Role definition ("You are a professional resume writer specializing in ATS-optimized resumes")
2. Constraints (no fabrication, professional tone, ATS-friendly formatting)
3. Output format (structured JSON matching Pydantic schema)
4. Few-shot examples (2-3 bullet transformations)
5. Specific instructions for this generation (target keywords, emphasis areas)

### Multi-Format Output
- Generate content once in structured JSON (format-agnostic)
- Render to PDF (WeasyPrint/Typst), DOCX (python-docx), LaTeX (Jinja2 templates), plain text
- The LLM step is format-independent; rendering is a separate pipeline

---

## 7. Recommended Architecture for JobRadar

### Pre-Generation
1. Extract keywords from JD (TF-IDF or LLM extraction)
2. Load user master profile from DB
3. RAG: retrieve 3 similar successful resumes (if outcome data exists)
4. Compose prompt with profile + JD + few-shot examples + keyword targets

### Generation
1. Call LLM (Claude Haiku or GPT-4o-mini) with structured output schema
2. Temperature 0.2-0.3 for resume, 0.4-0.6 for cover letter

### Post-Generation Guardrails (pipeline)
1. **Schema validation**: Pydantic model (Guardrails AI `ValidPydantic`)
2. **Fabrication check**: Compare extracted claims against profile (LLM-as-judge, ~$0.001)
3. **PII scan**: Regex patterns for SSN, credit card, etc.
4. **Keyword coverage**: Score 0-100 against JD keywords
5. **Length check**: Word count within limits
6. **Tone check**: Optional LLM-as-judge for professionalism

### Evaluation (CI/nightly)
1. promptfoo with golden test sets (145 cases)
2. Regression detection: flag if any task_type score drops >5%
3. Cost per full run: ~$0.30-$2.00

### Learning Loop
1. Track resume_version -> application -> outcome
2. After 50+ tracked outcomes, enable RAG-based few-shot retrieval
3. Surface insights on dashboard ("Quantified achievements correlate with 2x callbacks")
