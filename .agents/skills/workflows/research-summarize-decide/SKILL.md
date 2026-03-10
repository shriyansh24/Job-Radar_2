# Workflow: Research → Summarize → Decide

Investigation loop for tasks where the answer is not obvious. Gather
evidence, synthesize it into a structured brief, then make a decision
with an action plan.

---

## Purpose

Prevent premature implementation by front-loading research. Produce a
decision document with options, tradeoffs, and a recommended path
before any code is written.

## When to Use

- Evaluating libraries, frameworks, or architectural approaches
- Investigating unfamiliar codebases or modules
- Root cause is unclear (pre-step before `quick-fix` or `plan-implement-review`)
- Any decision that needs evidence before commitment

## When NOT to Use

- Task is well-understood and ready to implement (use `plan-implement-review`)
- Obvious single-file fix (use `quick-fix`)
- Pure implementation work with no open questions

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| Question | yes | What needs to be answered or decided |
| Constraints | no | Timeline, tech restrictions, must-haves |
| Acceptable uncertainty | no | How confident the answer needs to be (e.g., "80% is enough") |

## Outputs

| Output | Description |
|--------|-------------|
| Findings | Structured research notes with sources |
| Options | 2-4 options with tradeoffs |
| Recommendation | Preferred option with rationale |
| Next steps | Concrete action plan if recommendation is accepted |

## Steps

### Step 1: Research

**Persona:** Researcher (`core/personas/researcher`, id: `core.persona.researcher`)

1. Explore the codebase, documentation, and external sources
2. Gather relevant facts, patterns, and prior art
3. Cite internal sources (file paths, function names) where possible
4. Note gaps -- what could not be determined

**Output:** Research notes document.

### Step 2: Summarize

**Persona:** Specification (`core/personas/specification`, id: `core.persona.specification`)

1. Distill research notes into a structured brief
2. Identify 2-4 distinct options
3. For each option: describe, list pros/cons, estimate effort
4. Flag any assumptions or unknowns

**Output:** Decision brief.

### Step 3: Review

**Persona:** Reviewer (`core/personas/reviewer`, id: `core.persona.reviewer`)

1. Check the brief for logical gaps and unsupported claims
2. Verify cited sources are accurate
3. Identify risks not mentioned in the options
4. Suggest additional options if warranted

**Output:** Reviewed brief with annotations.

### Step 4: Decide

**Persona:** Planner (`core/personas/planner`, id: `core.persona.planner`)

1. Select the recommended option (or request more research)
2. Produce a concrete action plan: what to do, in what order
3. Define success criteria for the chosen approach
4. Identify when to revisit the decision

**Output:** Decision + action plan.

### Step 5: Quality Gate (optional)

**Capability:** Quality Gate (`quality/gate`, id: `quality.gate`)

Run the quality gate if the decision is high-stakes:
- Architecture changes affecting multiple teams/modules
- Vendor lock-in or irreversible migrations
- Security or compliance implications

### Step 6: Wrap-up

**Utility:** Wrap-up (`utilities/wrap-up`, id: `utilities.wrap-up`)

- Summarize the decision and rationale
- Record the decision as an ADR if appropriate
- Hand off the action plan to `plan-implement-review` for execution

## Handoff Templates

### Research Notes → Brief

```
## Research Notes

**Question:** <the question being investigated>
**Sources consulted:** <list of files, docs, URLs>

### Finding 1: <title>
<details>

### Finding 2: <title>
<details>

### Gaps
- <what could not be determined>
```

### Brief → Decision

```
## Decision Brief

**Question:** <restated>

### Option A: <name>
- Description: ...
- Pros: ...
- Cons: ...
- Effort: low/med/high

### Option B: <name>
- Description: ...
- Pros: ...
- Cons: ...
- Effort: low/med/high

### Recommendation
Option <X> because <rationale>.
```

### Decision → Action Plan

```
## Decision

**Chosen:** Option <X>
**Rationale:** <1-2 sentences>
**Success criteria:** <how to know it worked>

### Action Plan
1. <first step>
2. <second step>
3. ...

### Revisit if
- <condition that would invalidate this decision>
```

## Failure Modes

| Failure | Response |
|---------|----------|
| Insufficient information after research | Propose a targeted experiment or spike to fill the gap |
| All options have critical flaws | Reframe the question and re-run Step 1 with new constraints |
| Reviewer finds unsupported claims | Return to Step 1 for targeted follow-up research |
| Decision is blocked by external dependency | Document the blocker, set a check-in date, proceed with best available option |

## Example Run

```
Task: "Should we use SQLite-vec or Chroma for local vector search?"

Step 1 — Research (Researcher):
  - SQLite-vec: single-file, C extension, integrates with existing SQLite DB
  - Chroma: separate process, Python-native, more features (metadata filtering)
  - Existing codebase uses aiosqlite everywhere
  - Gap: no benchmarks for our dataset size (~50K vectors)

Step 2 — Summarize (Specification):
  Option A: SQLite-vec — low effort, single DB file, matches existing stack
  Option B: Chroma — more features, but adds a process dependency
  Option C: Both behind an interface — highest effort, maximum flexibility

Step 3 — Review (Reviewer):
  - Option A pros are solid; Chroma's extra features are unused today
  - Risk: SQLite-vec may struggle at 500K+ vectors (flag for revisit)

Step 4 — Decide (Planner):
  Chosen: Option A (SQLite-vec)
  Rationale: matches existing stack, no new dependencies, sufficient for MVP
  Revisit if: vector count exceeds 200K or metadata filtering becomes critical

Step 6 — Wrap-up:
  - Decision recorded
  - Action plan handed to plan-implement-review for implementation
```
