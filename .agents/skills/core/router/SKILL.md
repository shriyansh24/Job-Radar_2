# Router: Task → Persona / Workflow Selector

Routes incoming tasks to the appropriate persona(s), workflow, and capabilities.

---

## 1. Task Classification

Classify the task into one of these categories before selecting a workflow:

| Category | Signal | Examples |
|----------|--------|----------|
| **Engineering** | Build, fix, refactor, add feature | "Add rate limiting", "Fix login bug" |
| **Research** | Investigate, compare, evaluate, explore | "Which ORM should we use?", "How does auth work here?" |
| **Ops** | Deploy, configure, automate, schedule | "Set up CI", "Add a cron job" |
| **Quality** | Review, audit, test, benchmark | "Review this PR", "Run security audit" |
| **Specification** | Define, scope, clarify requirements | "What should the API look like?" |

## 2. Workflow Selection

```
Is the task trivial (1-2 files, obvious fix)?
  YES → quick-fix
  NO  →
    Is this an investigation / decision with no code output?
      YES → research-summarize-decide
      NO  → plan-implement-review (default)
```

| Workflow | id | When |
|----------|----|------|
| Plan → Implement → Review | `workflows.plan-implement-review` | Default for any multi-file change |
| Quick Fix | `workflows.quick-fix` | Single-file, obvious root cause |
| Research → Summarize → Decide | `workflows.research-summarize-decide` | Investigation, no code output |

## 3. Persona Selection

### Primary persona by phase

| Phase | Persona | id |
|-------|---------|----|
| Specify requirements | Specification | `core.persona.specification` |
| Plan implementation | Planner | `core.persona.planner` |
| Write code | Coder | `core.persona.coder` |
| Review changes | Reviewer | `core.persona.reviewer` |
| Write/run tests | Tester | `core.persona.tester` |
| Investigate/explore | Researcher | `core.persona.researcher` |
| Build AI/LLM features | AI Engineer | `core.persona.ai-engineer` |
| Design agent systems | AI Agents Architect | `core.persona.ai-agents-architect` |

### Specialist capabilities (add as needed)

| Need | Capability | id |
|------|------------|----|
| Security-sensitive change | Security Audit | `quality.security-audit` |
| Pre-merge check | Quality Gate | `quality.gate` |
| Agent evaluation | Agent Evaluation | `quality.agent-evaluation` |
| Multi-agent coordination | Orchestration | `orchestration.core` |

## 4. Routing Table (compact)

```
task_type        → workflow                    → personas              → gate?
─────────────────┬───────────────────────────┬──────────────────────┬───────
feature          │ plan-implement-review      │ plan,code,review,test│ opt
bugfix (complex) │ plan-implement-review      │ plan,code,review,test│ opt
bugfix (trivial) │ quick-fix                  │ code,test            │ no
refactor         │ plan-implement-review      │ plan,code,review,test│ opt
research         │ research-summarize-decide  │ research             │ no
security fix     │ plan-implement-review      │ plan,code,review,test│ YES
incident         │ incident-debug (playbook)  │ plan,research,code,  │ YES
                 │                            │ review               │
new skill        │ add-new-skill (playbook)   │ spec,code,review     │ opt
```

## 5. "Done" Checklist

Before delivering any result, verify:

- [ ] Requirement satisfied (acceptance criteria met or question answered)
- [ ] Tests run (or rationale documented for why not)
- [ ] Review performed (self-review minimum; persona review preferred)
- [ ] Wrap-up produced (summary, learnings, commit message)
- [ ] Quality gate passed (if security-sensitive or incident)
