# Workspace Semantic Execution Architecture Options v0.1

Status: **EVIDENCE-FIRST DESIGN COMPARISON / NON-AUTHORITATIVE**

Parent:
- `architecture/workspace-semantic-execution-migration.v0.1.md`
- `architecture/workspace-capability-workflow-inventory.v0.1.md`

Branch:
`workspace-semantic-execution-migration-v1`

## 1. Decision question

Workspace Control must preserve and extend autonomous knowledge work across research, engineering, data science, paper creation, presentations, tutoring, coursework, documents, and operations while frontier-model allowance becomes a scarce schedulable resource.

The immediate architecture question is not:

> Which agent framework should replace Workspace Control?

It is:

> Which decomposition of semantic state, cognitive reasoning, authority, durable execution, artifact/provenance state, and executor/resource routing best preserves the current system's behavior while minimizing migration risk and frontier-model usage?

The current "semantic graph + deterministic authority + heterogeneous executor router + durable execution kernel" proposal is a design hypothesis. This document compares materially different alternatives before implementation freeze.

No option in this document grants execution authority.

---

## 2. Evidence sources

### Existing workspace evidence

The comparison is constrained by existing proven behavior in:

- `workspace-control`
- `research-engine`
- `PADataset`
- `MTH602-AdamTrott`
- `EAS501-AdamTrott`
- `CIS560-AdamTrott`

and by:

- task capsules;
- tutoring contract;
- operator/portability contracts;
- document-artifact workflow;
- evidence-first solution research;
- research knowledge ontology;
- research-engine durable orchestration;
- GitRunner typed controller/root protocol;
- Workspace Shell bounded execution;
- recent Instant worker concurrency/recovery experiments.

### External architecture evidence

The following systems were reviewed as architecture evidence, not as automatic dependencies.

#### Temporal Durable Execution

Official Temporal documentation describes an Event History as the complete durable log used to recover workflow state after crashes. Workflow code schedules Activities/Timers rather than performing external side effects directly; replay reconstructs state and resumes without repeating completed effects.

Temporal's current Durable AI guidance explicitly targets:

- long-running stateful agent loops;
- LLM/tool calls;
- human approval waits;
- multi-day pauses;
- fan-out pipelines;
- shared worker/task-queue infrastructure.

Relevant sources:
- https://docs.temporal.io/encyclopedia/event-history
- https://docs.temporal.io/workflows
- https://docs.temporal.io/ai
- https://go.temporal.io/platform-hub/ai-engineering/ai-reference-architecture

#### Dapr Workflow / Dapr Agents

Dapr Workflow is a durable execution engine built on the Durable Task Framework. Its architecture separates deterministic orchestration from activities; history/state is persisted and used to resume after crashes/restarts. The current Dapr Agents documentation describes workflow-backed durable agents whose LLM/tool interactions are persisted and recoverable.

Relevant sources:
- https://docs.dapr.io/developing-applications/building-blocks/workflow/workflow-overview/
- https://docs.dapr.io/developing-applications/building-blocks/workflow/workflow-architecture/
- https://docs.dapr.io/developing-ai/dapr-agents/dapr-agents-introduction/

#### LangGraph

LangGraph's current documentation uses explicit graph state and checkpointing. Its guidance recommends storing raw state rather than formatted prompts, placing durable checkpoints at node boundaries, representing retries/interrupts as workflow behavior, and resuming using a persistent thread/checkpointer.

This is directly relevant to resumable Instant reasoning and bounded context construction.

Relevant source:
- https://docs.langchain.com/oss/javascript/langgraph/thinking-in-langgraph

#### Microsoft Agent Framework

Microsoft Agent Framework currently provides:

- functional/graph workflows;
- agents as workflow executors;
- checkpoint/resume;
- shared/pending state capture;
- human-in-the-loop;
- sequential/concurrent/handoff/group-chat/Magentic orchestration.

Magentic uses a manager with a progress ledger, replanning and stall detection for open-ended work. Current documentation marks some orchestration functionality as experimental, so it is stronger as design evidence than as an immediate foundational dependency.

Relevant sources:
- https://learn.microsoft.com/agent-framework/overview
- https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints
- https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/magentic/

#### Open Policy Agent

OPA explicitly separates the Policy Decision Point from Policy Enforcement Points and accepts structured data for policy decisions. This supports retaining Workspace Control's existing rule that cognitive/model output may propose work but cannot manufacture execution authority.

Relevant source:
- https://www.openpolicyagent.org/docs
- https://www.openpolicyagent.org/docs/deploy

#### W3C PROV-O

PROV-O defines generic provenance primitives:

- Entity;
- Activity;
- Agent;
- Plan;
- use/generation/association/derivation relations.

It is explicitly extensible for application-specific provenance. This supports mapping Workspace Control's project-specific objects onto a smaller stable provenance core rather than inventing every lineage concept from scratch.

Relevant source:
- https://www.w3.org/TR/prov-o/

#### AI Scientist / AI Scientist v2

AI Scientist and AI Scientist v2 demonstrate full research loops including idea/hypothesis generation, implementation, experiment execution, analysis/visualization, manuscript creation, and review. v2 uses progressive agentic tree search managed by an experiment-manager agent.

Relevant sources:
- https://arxiv.org/abs/2408.06292
- https://arxiv.org/abs/2504.08066

#### AFlow

AFlow treats agent-workflow design itself as a search/optimization problem and uses execution feedback to iteratively improve code-represented workflows. It is evidence that workflow topology should not be assumed permanently static.

Relevant source:
- https://arxiv.org/abs/2410.10762

---

## 3. Requirements against which options are evaluated

A viable architecture must preserve or improve:

1. project-local domain authority;
2. non-authoritative cognitive reasoning;
3. deterministic execution authority;
4. exact provenance;
5. contradiction and supersession handling;
6. durable task recovery;
7. disposable workers;
8. worker death recovery;
9. async waits with zero reasoning burn;
10. open-world workflow/domain extensibility;
11. executor/harness identity;
12. capability-based routing;
13. reasoning-tier routing;
14. cost/quota/allowance routing;
15. bounded context construction;
16. semantic caching;
17. GitHub-native engineering workflows;
18. Lambda CPU/GPU execution;
19. artifact build/render/visual QA;
20. tutoring/mastery semantics;
21. paper/presentation semantics;
22. research/experiment semantics;
23. no manual SHA/log/JSON transport;
24. gradual migration and rollback;
25. completion within the November migration window.

---

## 4. Architecture family A — Minimal evolution of current Workspace Control

### Shape

Keep current architecture largely unchanged:

```text
project repos
→ workspace-control task capsules/workflow descriptors
→ current controllers/research-engine
→ existing executors
```

Add only:

- executor registry;
- cost/quota metadata;
- routing policy;
- resumable Instant adapter;
- context compression.

### Advantages

- lowest initial migration cost;
- preserves all existing policy/task semantics;
- minimal production risk;
- easiest to finish quickly;
- current GitRunner/Workspace Shell remain unchanged.

### Weaknesses

- semantic state remains scattered across Markdown/JSON/project-specific files;
- research, tutoring, publication, and engineering workflows retain separate ad hoc representations;
- difficult to query cross-workflow state;
- hard to make generic decomposition/routing decisions;
- cognitive continuity may continue to depend on hand-authored context files;
- future workflow growth continues to create coordination debt.

### Frontier-usage impact

Moderate improvement. A router can reduce frontier use, but weak shared semantic state limits context compression and reusable reasoning.

### Assessment

Useful as rollback baseline and potentially as the first migration step, but unlikely to achieve the full long-term goal alone.

---

## 5. Architecture family B — Generalize research-engine into the universal kernel

### Shape

Promote research-engine's existing PostgreSQL job/worker/lease system into the shared workspace runtime.

```text
workspace-control authority/policy
        ↓
generalized research-engine queue
        ↓
workers/executors
        ↓
project artifacts/results
```

Generalize:

- ResearchJob -> WorkItem / ActionAttempt;
- JobType -> extensible action/workflow descriptors;
- ExecutorTier -> capability/resource profile;
- research_runs -> programs/workflows;
- worker leases/retries -> universal execution.

### Advantages

- existing durable PostgreSQL state;
- existing worker leasing/retry semantics;
- already handles deterministic + semantic executors;
- familiar deployment/runtime;
- lower dependency count than adopting a new workflow system;
- strong fit for long-running model/data workloads.

### Weaknesses

- research-engine currently owns project-specific executable research behavior;
- promoting it to workspace infrastructure changes its ownership boundary substantially;
- current job taxonomy and orchestration logic are research-specific;
- authority semantics would need careful separation from queue state;
- project repositories currently route through workspace-control, not research-engine;
- risks turning one project implementation into a monolithic platform.

### Frontier-usage impact

Potentially high improvement if context/routing are generalized.

### Assessment

A credible implementation source for durable execution primitives, but risky as the sole universal control plane.

---

## 6. Architecture family C — Graph-first semantic execution platform

### Shape

Make a typed semantic graph the primary coordination abstraction.

```text
project-local authoritative records
        ↓
provenance-preserving semantic projection
        ↓
candidate cognitive graph
        ↓
authority projection
        ↓
execution graph
        ↓
executor router
        ↓
result/evidence projection
        ↺
```

### Advantages

- strong cross-domain semantics;
- naturally represents dependencies, evidence, findings, revisions, artifacts, mastery, hypotheses and decisions;
- bounded graph slices enable context compression;
- durable reasoning outputs can be cached as semantic objects;
- supports open-world domain extensions;
- good foundation for "why?" queries and provenance;
- can represent dynamic graph expansion and recursive decomposition.

### Weaknesses

- highest risk of overbuilding;
- graph projection can become a competing source of truth if boundaries are weak;
- graph storage/query technology can distract from actual workflow migration;
- execution semantics still need another reliable substrate;
- ontology versioning/migration is nontrivial;
- a full graph-first rewrite is unlikely to be safely completed in one month.

### Frontier-usage impact

Potentially highest long-term reduction because of precise context selection and reusable semantic state.

### Assessment

Strong semantic architecture but should be introduced as a projection/interface layer, not immediately as the sole authoritative runtime.

---

## 7. Architecture family D — External durable-workflow engine as execution kernel

Candidate substrates include Temporal or Dapr Workflow.

### Shape

```text
semantic/cognitive layer
        ↓
deterministic authority
        ↓
Temporal/Dapr workflow
        ↓
activities
  GitHub / Lambda / models / artifacts
```

### Advantages

- mature durable execution semantics;
- explicit event history;
- crash recovery;
- long waits;
- timers/events;
- retries;
- child workflows;
- worker scaling;
- strong observability;
- less custom scheduler/recovery code.

### Weaknesses

- new operational infrastructure;
- deterministic replay constraints;
- duplicate durable state alongside Git/GitHub/task capsules;
- migration of existing controller/research-engine semantics is substantial;
- authority still needs Workspace Control policy;
- GitRunner generation fencing and project-specific resource isolation remain custom;
- high November integration risk.

### Frontier-usage impact

Indirect. Excellent at eliminating polling/repeated work, but does not itself solve model selection or semantic context.

### Assessment

Excellent reference architecture and possible future substrate. Immediate replacement of existing durable execution is not justified without a focused spike proving enough benefit to offset migration complexity.

---

## 8. Architecture family E — Agent framework as primary cognitive/workflow runtime

Candidates include LangGraph, Microsoft Agent Framework, or Dapr Agents.

### Shape

```text
agent/workflow graph
→ model/tool nodes
→ checkpoint/resume
→ project actions
```

### Advantages

- native model/agent abstractions;
- built-in checkpoint/resume;
- subagents/concurrency;
- human-in-the-loop;
- dynamic routing/replanning;
- easier resumable Instant/frontier model experiments;
- less custom cognitive-loop code.

### Weaknesses

- their graph/workflow state is not Workspace Control authority;
- framework semantics evolve rapidly;
- no framework directly models our scientific/tutoring/paper authority boundaries;
- external frameworks cannot be allowed to widen tool authority;
- GitRunner/Lambda security remains separate;
- may duplicate the semantic ontology and durable execution systems.

### Frontier-usage impact

Potentially strong if checkpointing/context management and agent decomposition are good.

### Assessment

Good candidate for a cognitive-executor adapter or experimental orchestration backend, not the authoritative core.

---

## 9. Architecture family F — Hybrid semantic projection + existing execution substrates

### Shape

Preserve current authoritative/project systems and add a general semantic/resource layer above them.

```text
PROJECT-LOCAL AUTHORITATIVE RECORDS
        │
        ├─ PADataset
        ├─ course repos
        ├─ research-engine
        └─ workspace-control policies/tasks
        │
        ▼
REBUILDABLE SEMANTIC PROJECTION
        │
        ├─ goals/questions/findings
        ├─ artifacts/revisions
        ├─ capabilities/reasoning requirements
        └─ candidate actions
        │
        ▼
DETERMINISTIC AUTHORITY / ELIGIBILITY
        │
        ▼
HETEROGENEOUS ROUTER
        │
        ├─ deterministic
        ├─ Instant
        ├─ local model
        ├─ subscription model
        ├─ frontier
        └─ human
        │
        ▼
EXISTING DURABLE EXECUTION SUBSTRATES
        │
        ├─ Git/GitHub task state
        ├─ GitRunner typed controller/root protocol
        ├─ Workspace Shell
        ├─ research-engine durable jobs
        └─ deterministic project workflows
        │
        ▼
RESULT / ARTIFACT / RECEIPT
        │
        └────────────→ semantic projection
```

### Advantages

- preserves already validated authority boundaries;
- semantic graph remains rebuildable rather than authoritative;
- does not require immediate scheduler replacement;
- lets research-engine remain a project runtime while exposing reusable patterns;
- GitRunner and Workspace Shell remain proven bounded execution surfaces;
- supports incremental migration workflow by workflow;
- enables Instant/resumable reasoning without changing live infrastructure first;
- leaves open a later Temporal/Dapr adoption if durable-runtime benchmarks justify it;
- directly aligns with existing research knowledge ontology's authority firewall.

### Weaknesses

- temporarily retains multiple durable state stores;
- requires reliable projection/adapters;
- cross-store reconciliation rules must be explicit;
- risk of architecture complexity if the semantic projection grows too broad;
- still requires careful executor/resource router design.

### Frontier-usage impact

High. Bounded semantic slices + resumable cheap workers + existing deterministic execution can reduce frontier use without waiting for a wholesale runtime rewrite.

### Assessment

**Preferred migration hypothesis**, not yet a frozen architecture.

It gives the largest near-term leverage while preserving rollback and existing accepted infrastructure.

---

## 10. Comparative matrix

Scoring:
- 5 = strong
- 3 = moderate
- 1 = weak/high-risk

| Requirement | A Minimal | B Research-engine kernel | C Graph-first | D Temporal/Dapr | E Agent framework | F Hybrid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| November migration feasibility | 5 | 3 | 2 | 1 | 3 | 5 |
| preserve current authority | 5 | 3 | 3 | 4 | 2 | 5 |
| preserve project-local truth | 5 | 3 | 4 | 5 | 3 | 5 |
| open-world workflow extensibility | 2 | 4 | 5 | 4 | 4 | 5 |
| durable execution/recovery | 3 | 4 | 2 | 5 | 4 | 4 |
| resumable model reasoning | 3 | 4 | 5 | 5 | 5 | 5 |
| provenance/semantic traceability | 3 | 4 | 5 | 4 | 3 | 5 |
| cost/quota-aware routing | 4 | 4 | 5 | 3 | 4 | 5 |
| bounded context / semantic cache | 2 | 3 | 5 | 3 | 4 | 5 |
| GitRunner/Workspace Shell reuse | 5 | 3 | 3 | 3 | 3 | 5 |
| rollback/migration safety | 5 | 3 | 2 | 2 | 3 | 5 |
| low new operational complexity | 5 | 4 | 3 | 1 | 3 | 4 |
| future substrate flexibility | 2 | 3 | 3 | 3 | 2 | 5 |

This matrix is an engineering judgment based on current evidence, not a benchmark result.

---

## 11. Preferred migration hypothesis

The strongest current hypothesis is **family F: hybrid semantic projection + existing execution substrates**.

That does **not** mean "build a giant graph database first."

The minimum version is:

1. keep project-local authoritative records;
2. keep current task capsules/policies;
3. keep GitRunner and Workspace Shell;
4. keep research-engine's existing research execution;
5. define a small general semantic projection contract;
6. define resumable reasoning-state objects;
7. define capability/reasoning/context requirements;
8. define executor/resource/quota registry;
9. route bounded actions to the cheapest sufficient executor;
10. persist results back to owning records and rebuild the projection.

This can be implemented incrementally and benchmarked before any replacement of current durable execution.

---

## 12. External-framework adoption rule

Do not adopt a framework because it overlaps conceptually.

An external runtime/framework earns production adoption only if a bounded benchmark demonstrates a material advantage in at least one of:

- fewer custom correctness-critical lines;
- stronger crash/recovery semantics;
- lower operational burden;
- better context/allowance efficiency;
- better dynamic workflow behavior;
- better observability;
- easier extension;
- lower failure rate;

without weakening:

- authority;
- provenance;
- project isolation;
- rollback;
- exact resource binding;
- workflow coverage.

### Candidate focused spikes

#### Temporal/Dapr spike

Implement one synthetic resumable workflow with:

- independent child actions;
- async wait;
- worker death;
- duplicate completion;
- cancellation;
- bounded retry;
- external event;
- exact artifact receipt.

Compare against current research-engine/Git/GitRunner semantics.

#### LangGraph/Agent Framework spike

Implement one resumable cognitive workflow:

- decompose;
- checkpoint;
- resume with fresh model invocation;
- branch;
- independent critic;
- synthesize;
- external wait;
- resume.

Compare context size, state clarity, recovery, and model usage against a custom Workspace Control reasoning-node representation.

Neither spike authorizes production replacement.

---

## 13. Resumable Instant reasoning hypothesis

The current design hypothesis is:

> A disposable Instant invocation can advance a durable reasoning process by one bounded quantum; long-horizon cognition emerges from durable state + repeated event-driven invocations.

This must be benchmarked separately from model intelligence.

### Hypothesis H1 — horizon equivalence

For tasks where every bounded reasoning node is within Instant capability, repeated fresh/resumed Instant invocations can match a stronger long-lived model's final workflow effectiveness.

### Hypothesis H2 — decomposition recovers capability

Some tasks that fail as one large Instant request become solvable after decomposition into independently verifiable leaves plus bounded synthesis.

### Hypothesis H3 — intrinsic difficulty remains

Repeated continuation does not reliably compensate when the remaining node requires reasoning beyond Instant's intrinsic capability.

### Required benchmark arms

```text
A — frontier long-horizon loop

B — Instant persistent-chat continuation

C — Instant stateless durable resumptions

D — Instant decomposition + independent critique/synthesis

E — hybrid Instant + frontier escalation only for hard residuals
```

Metrics:

- final task correctness;
- scientific/engineering validity;
- invalid branches pursued;
- iterations;
- human corrections;
- provenance violations;
- context tokens supplied;
- frontier allowance consumed;
- wall-clock execution;
- deterministic work performed;
- number of escalations;
- reviewer acceptance.

The desired architecture is not the one with zero frontier use. It is the one that minimizes scarce frontier use while preserving accepted output quality.

---

## 14. Implication for the unfinished GitRunner migration

The GitRunner migration should continue as an independent bounded infrastructure workstream.

It should not wait for the entire semantic redesign because:

- the typed v3 protocol is already validated;
- the first control-small canary is accepted;
- PADataset CPU/GPU migration remains unfinished;
- the future semantic layer needs a reliable execution substrate regardless of which architecture family wins.

However:

- no semantic redesign task may manufacture canary authority;
- Workspace Shell acceptance evidence only clears its dependency;
- fresh exact one-shot `padataset-cpu-public-v1` authority is still required;
- Research GPU-derived classes remain NO_BY_DEFAULT unless separately reopened.

This keeps infrastructure completion parallel to design research without conflating authorities.

---

## 15. Current recommendation

Proceed on two parallel but authority-separated tracks.

### Track 1 — finish proven infrastructure migration

- preserve existing GitRunner task;
- reconcile Workspace Shell acceptance evidence;
- prepare, review, and only when explicitly authorized execute next PADataset canaries;
- do not redesign the already validated typed controller protocol merely because the upper-layer architecture is changing.

### Track 2 — build successor architecture evidence

- expand workflow inventory;
- freeze small semantic core;
- define resumable reasoning process;
- define executor/resource/quota ontology;
- benchmark Instant decomposition/resumption;
- run external-runtime spikes only where they may remove significant custom infrastructure;
- migrate workflow families incrementally.

The tracks meet at a typed execution adapter boundary rather than through shared implicit state.

---

## 16. Decision status

Current status:

```text
architecture family F
= PREFERRED_MIGRATION_HYPOTHESIS

NOT:
= FROZEN
= PRODUCTION_AUTHORIZED
= EXECUTION_AUTHORITY
```

Required before architecture freeze:

1. complete capability/workflow inventory to representative coverage;
2. independently review this comparison;
3. define semantic core + extension contract;
4. benchmark resumable Instant reasoning;
5. perform at least one bounded external-runtime comparison or document why the expected benefit is insufficient to justify a spike;
6. define migration acceptance suite;
7. prove the hybrid path can represent one unseen/new workflow without kernel change.
