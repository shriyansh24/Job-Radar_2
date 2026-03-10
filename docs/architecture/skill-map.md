# Skill Map

> How to navigate the `.agents/skills/` taxonomy.

---

## Start Here: `entrypoints/`

Entrypoints are curated redirects -- thin stubs that tell you which canonical
skill to load and when. They do not contain full instructions.

```
entrypoints/
  personas/        → which persona to use for which phase
  workflows/       → which workflow to follow for which task type
  playbooks/       → pre-built chains of personas for common scenarios
```

Pick an entrypoint, follow its pointer to the canonical skill, load that.

## Router: `core/router`

If you are unsure which entrypoint to use, start with the **Router**
(`core/router`, id: `core.router`). It provides:

- Task classification rules
- A decision tree for workflow selection
- A routing table mapping task types to personas
- A "done" checklist

## Personas: `core/personas/*`

The agents that do the work. Each persona has a defined role, toolset, and
operating style.

| Persona | id | Role |
|---------|----|------|
| Planner | `core.persona.planner` | Break tasks into steps |
| Coder | `core.persona.coder` | Write and modify code |
| Reviewer | `core.persona.reviewer` | Review for correctness and security |
| Tester | `core.persona.tester` | Write and run tests |
| Researcher | `core.persona.researcher` | Investigate and gather context |
| Specification | `core.persona.specification` | Translate requirements into specs |
| AI Engineer | `core.persona.ai-engineer` | Build LLM/RAG applications |
| AI Agents Architect | `core.persona.ai-agents-architect` | Design agent systems |

## Capabilities

Skills that provide specific functionality. Personas call these as needed.

| Area | Path | Examples |
|------|------|----------|
| Engineering | `engineering/*` | backend, api, testing, security, performance, tooling |
| Orchestration | `orchestration/*` | swarm, consensus, coordination, optimization, task-routing |
| Memory | `memory/*` | memory-management, embeddings, mcp, systems, coordination |
| Quality | `quality/*` | code-review, security-audit, agent-evaluation, gate |
| Ops | `ops/*` | agent-manager, hooks-automation, workflow-automation, claims |

## Workflows: `workflows/*`

Structured multi-step processes that chain personas together.

| Workflow | id | When |
|----------|----|------|
| Plan → Implement → Review | `workflows.plan-implement-review` | Default for any multi-file change |
| Quick Fix | `workflows.quick-fix` | Trivial single-file fixes *(stub only)* |
| Research → Summarize → Decide | `workflows.research-summarize-decide` | Investigation tasks *(stub only)* |

## Integrations: `platform/*`, `products/*`

| Area | Path | Examples |
|------|------|----------|
| Platform | `platform/*` | github, azure-agents |
| Products | `products/*` | agentdb, hive-mind, flow-nexus, reasoningbank |

## Knowledge: `reference/*`, `architecture/*`, `context/*`

| Area | Path | Examples |
|------|------|----------|
| Reference | `reference/*` | clean-code, api-patterns, backend-dev-guidelines |
| Architecture | `architecture/*` | architect-review, architecture-decision-records |
| Context | `context/*` | context-fundamentals, context-compression |

## Utilities / Ops: `utilities/*`, `ops/*`

| Area | Path | Examples |
|------|------|----------|
| Utilities | `utilities/*` | wrap-up, smart-commit, deslop, skill-builder, find-skills |
| Ops | `ops/*` | agent-manager, hooks-automation, pro-workflow, claims-authorization |

## Profiles: `platforms/profiles/`

Pre-configured policy bundles that control which personas, workflows, and
gates are available.

| Profile | Gate required? | Personas | Depth |
|---------|---------------|----------|-------|
| `fast` | no | coder, tester | short |
| `safe` | yes | planner, coder, reviewer, tester, spec | medium |
| `deep` | yes | all 8 personas | deep |

---

## Typical Run: Plan → Implement → Review

```
1. Router classifies task as "engineering / feature"
2. Router selects workflow: plan-implement-review
3. Workflow Step 1: Planner produces a step plan
4. Workflow Step 2: Coder implements the plan
5. Workflow Step 3: Reviewer checks the changes
6. Workflow Step 4: Tester writes and runs tests
7. Workflow Step 5: Wrap-up summarizes and commits
8. (Optional) Quality Gate runs final checks
```

See `workflows/plan-implement-review/SKILL.md` for the full definition.
