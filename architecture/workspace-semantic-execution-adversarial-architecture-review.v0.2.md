# Workspace Semantic Execution — Adversarial Architecture Review v0.2

Status: **SECOND-PASS RESEARCH REVIEW / FREEZE INVARIANTS ONLY**

Parent task: `workspace-semantic-execution-migration-v1`

Date: 2026-11-13

## 1. Review method

This pass deliberately does not ask the same model to merely "review its answer."

The current architecture was attacked through independent evidence lenses:

- production agent-harness source-code studies;
- long-horizon / multi-scale reasoning research;
- durable-execution runtime architecture;
- SRE simplicity and operability guidance;
- distributed-system formal methods;
- property-based state-machine testing;
- fault-injection/chaos engineering;
- hexagonal/evolutionary software architecture;
- observability and resource-isolation mechanisms.

The goal is not consensus. The goal is to expose assumptions that would otherwise fail weeks later.

## 2. Findings that materially change or sharpen the design

### F1 — Separate custom harness logic from durable-execution plumbing

Production coding-agent harnesses frequently use small, explicit host-language loops rather than general-purpose agent frameworks. A 2026 source-code study of eleven production systems found no use of LangChain/LangGraph/AutoGen/CrewAI/etc. in the core runtime and emphasized debuggability/transparency over abstraction.

This does **not** imply hand-building distributed durability.

The correct split is:

- hand-write the Workspace-specific cognitive/task/action state machine because that is our domain logic;
- use a mature durable-execution substrate for checkpoints, retries, waits, messages, recovery, and queue flow control;
- keep the durable substrate behind a port.

Therefore:
- no LangGraph-style framework dependency in the domain core by default;
- no custom replay/event-sourcing engine by default;
- DBOS remains the leading first runtime spike;
- Restate remains the strongest alternative;
- Temporal remains the mature reference/escape hatch.

### F2 — Start as a modular monolith, not a microservice system

The first backend should be one deployable control-plane application with strong internal module boundaries.

Reason:
- SRE evidence strongly correlates simplicity with reliability;
- distributed boundaries create failure modes, versioning, networking, deployment and observability costs;
- current workload does not justify independent service scaling.

Initial external processes are only where the boundary already exists:
- PostgreSQL;
- browser/operator bridge;
- GitHub/CI/external tools;
- optional project-specific executors.

No Kafka, Redis, Neo4j, vector DB, service mesh, Kubernetes, or separate agent-service fleet in the first implementation.

### F3 — Stop using Git/GitHub as the hot runtime database

Git remains excellent for:
- authoritative project/task contracts;
- source;
- immutable implementation checkpoints;
- artifacts and architecture decisions;
- exported audit snapshots.

It should not own high-frequency scheduler state:
- leases;
- generations;
- ready queues;
- heartbeats;
- transient retries;
- session lifecycle;
- every reasoning quantum.

Those belong in the runtime database/durable runtime.

Git synchronization should occur at semantically meaningful checkpoints, not every internal transition.

This directly reduces branch-CAS races, CI latency, and the class of errors experienced in the existing controller.

### F4 — Multi-agent is conditional, not the default

Research and production experience show multi-agent architectures are valuable for genuinely parallel breadth, but coordination cost rises quickly.

Anthropic reports multi-agent research using roughly 15× chat token volume in its system and notes that tightly coupled tasks are poor candidates.

Therefore the default process is:
- one logical ReasoningProcess;
- recursively fork only when independent context isolation or parallelism has a concrete benefit;
- keep tactical children bounded;
- avoid peer-to-peer agent meshes;
- communicate through typed state/artifact refs.

### F5 — Context management is a first-class subsystem

Long-horizon research repeatedly identifies context saturation/irrelevance as a core failure mode.

The system needs:
- level-specific context (strategic/tactical/operational);
- JIT retrieval from identifiers/references;
- compact durable working state;
- recent-tail preservation;
- explicit compaction policy;
- provenance-preserving summaries.

Persistent chats are caches, not canonical memory.

For code/workspace state, deterministic structural retrieval (paths, Git, grep, symbols, exact file refs) should precede embeddings.

### F6 — Formalize the tiny dangerous kernel

The full AI system is too open-ended for formal verification.

The orchestration kernel is small enough to model:
- work-state transitions;
- dependency readiness;
- claim/lease ownership;
- generation fencing;
- stale-worker rejection;
- retry/idempotency;
- wait/wake;
- action completion;
- compensation;
- terminality.

Use TLA+ (or equivalent) for design-level safety/liveness invariants.

Then use property-based state-machine testing (Hypothesis) against the executable implementation, generating long sequences of claims, failures, retries, restarts, acknowledgments and stale events.

This is explicitly targeted at "bugs no one thought to write a test for."

### F7 — Fault injection belongs in development, not after deployment

The controller's historical failure mode was expansion into states that the original assumptions never exercised.

The new backend should include deterministic fault points from the beginning:
- process death after claim;
- process death after external effect but before checkpoint;
- duplicate event;
- delayed event;
- out-of-order event;
- stale generation;
- database disconnect/reconnect;
- executor disappearance;
- validator timeout;
- browser/session loss;
- CI callback duplication;
- partial external effect.

Fault tests must have stop conditions and recovery assertions.

### F8 — Architecture must have executable fitness functions

Architectural properties must be continuously tested, not documented only in prose.

Examples:
- domain core has no DBOS/Restate/Temporal imports;
- domain core has no GitHub/browser/database-specific imports;
- no model output can create AuthorityDecision;
- CandidateAction cannot execute without ActionSpec;
- ActionSpec cannot COMPLETE without a ValidationResult/postcondition;
- stale generation cannot transition current work;
- current-state tables cannot accept impossible transitions;
- semantic projection is rebuildable;
- runtime can restart with no duplicate validated effect;
- control plane uses zero GPU;
- resource budgets remain under defined limits;
- unknown extensions fail closed.

These are architecture fitness functions.

## 3. Architecture freeze boundary

### Freeze now

Freeze these invariants/interfaces:

1. External multi-scale cognitive process: strategic / tactical / operational.
2. Context manager / packet compiler is a first-class component.
3. Typed durable state is primary coordination; free-form agent-to-agent prose is not.
4. CandidateAction -> AuthorityDecision -> ActionSpec is a deterministic trust boundary.
5. Tool success is not completion; observed postcondition/validation is required.
6. Durable-runtime semantics live behind `DurableRuntimePort`.
7. Hot runtime control state is not stored in Git.
8. Semantic graph is derived/rebuildable and cannot grant authority.
9. Model/provider identity is a replaceable executor profile.
10. Control plane is GPU-free by default.
11. Architecture evolves through explicit fitness tests, ADRs, assumption records, and real-workflow evidence.

### Do not freeze yet

Do not permanently freeze:
- DBOS vs Restate vs Temporal;
- PostgreSQL forever;
- graph database vs relational semantic projection;
- vector retrieval;
- exact memory compaction algorithm;
- exact Instant decomposition/escalation thresholds;
- number of workers;
- specific backend language beyond first spike;
- specific policy language;
- specific UI/session implementation.

## 4. First implementation architecture

### Shape

One modular control-plane application:

```text
semantic-execution/
  domain/
    work/
    reasoning/
    decisions/
    actions/
    authority/
    validation/
    resources/
  application/
    orchestrator/
    packet_compiler/
    action_compiler/
    session_broker/
  ports/
    durable_runtime.py
    state_store.py
    semantic_projection.py
    executor.py
    authority.py
    telemetry.py
    clock.py
  adapters/
    dbos/
    postgres/
    github/
    workspace_shell/
    operator_bridge/
    ci/
  tests/
    unit/
    state_machine/
    contract/
    fault/
    workflow/
```

This is a logical layout, not a required language/package syntax.

### First runtime candidate

DBOS + PostgreSQL.

Why:
- open-source library in process;
- no separate orchestrator needed for the initial deployment;
- checkpoints/queues/messages are Postgres-backed;
- one Postgres vCPU is documented as supporting roughly 1,000 workflow/step checkpoints per second as a rule of thumb, vastly above expected human/ChatGPT-worker orchestration rates;
- transactional state + durability can remain close;
- supports durable agent workflows and human-in-the-loop.

Keep `DurableRuntimePort` so the application does not know DBOS-specific types.

### Challenger

Restate if the first real workflow shows:
- long-suspension semantics are awkward;
- keyed session actors would materially simplify lifecycle;
- durable RPC/callbacks dominate;
- Postgres polling/coordination is undesirable.

### Temporal trigger

Evaluate Temporal if:
- many independent durable services emerge;
- operational visibility/versioning requirements become platform-scale;
- DBOS/Restate limitations force us to implement missing workflow machinery ourselves.

## 5. Compute / "fuel" model

The engine has four separate resource pools.

### A. Reasoning compute

Primary:
- ChatGPT GPT-6 Instant remote inference.

This consumes OpenAI-side compute / plan quotas, not local GPU VRAM.

The scheduler tracks reasoning as a resource pool:
- executor identity;
- available sessions;
- observed quota state where knowable;
- concurrent human-service capacity;
- task value/priority;
- number of reasoning quanta.

### B. Control-plane compute

Expected workload:
- scheduler;
- DBOS runtime;
- Postgres queries;
- context compilation;
- state transitions;
- telemetry.

This is CPU/RAM/disk I/O work.

**Hard design requirement: zero CUDA dependency and zero GPU allocation.**

On Linux:
- launch control-plane processes with `CUDA_VISIBLE_DEVICES=""`;
- systemd/cgroup resource limits provide CPU and memory ceilings;
- GPU executors run as separate resource classes.

Initial fitness targets (provisional, measured on real workload):
- GPU VRAM: 0 bytes for control plane;
- app + orchestration steady CPU: << 1 full CPU core under normal human-scale load;
- control-plane burst: no more than 2 logical CPU cores without explicit workload reason;
- app + orchestration RSS target: <= 1 GiB;
- PostgreSQL memory separately budgeted and tuned;
- no idle busy-poll loops;
- WAITING_EXTERNAL consumes no model inference and negligible CPU.

These are targets, not assumed facts. Measurement decides whether they tighten/relax.

### C. Effect compute

Project work may consume:
- local CPU;
- local GPU;
- GitHub Actions;
- remote services;
- experiments.

This is **not** the control plane.

Each effect executor receives an explicit `ResourceLease` / `ResourceRequirement`.

Local GPU work is opt-in and assigned by executor adapter. The scheduler never assumes a GPU is free merely because it exists.

### D. Human attention

Human paste/submit/judgment is a scarce resource and must be scheduled like one.

The backend should minimize:
- required interventions;
- context reconstruction;
- repeated judgment;
- unnecessary worker launches.

## 6. Resource isolation

Control plane:
- `CUDA_VISIBLE_DEVICES=""`;
- systemd `CPUQuota`, `MemoryHigh`, `MemoryMax`, `TasksMax`;
- separate service account/working directory where practical.

Heavy executor:
- separate service/process;
- explicit GPU visibility;
- explicit concurrency;
- resource lease;
- cancellable;
- effect receipt.

This means a runaway research job can be killed without killing scheduler state, and a scheduler bug cannot silently consume the GPUs.

## 7. Reliability engineering program

### Design-time
- ADR for every hard-to-reverse decision.
- Assumption Register for every material unproven assumption.
- TLA+ model for orchestration kernel.
- versioned schemas.
- ports/adapters dependency direction.

### Implementation-time
- unit tests for pure domain transitions;
- contract tests for every adapter;
- property-based state-machine tests;
- deterministic fake clock;
- deterministic fake durable runtime;
- failure injection around every effect/checkpoint boundary;
- migrations tested forward and backward where feasible.

### Integration
- shadow mode first: plan/compile actions without executing;
- dry-run adapters where upstream supports them;
- read-only execution before mutation;
- one capability/action family enabled at a time;
- canary work items;
- exact postcondition validators.

### Operations
- OpenTelemetry trace per ReasoningProcess/Action;
- structured logs;
- bounded metric cardinality;
- runtime health endpoint;
- queue depth / stuck work / retry metrics;
- resource metrics;
- no success without receipt + validator evidence.

## 8. Assumption Register

Every material assumption should be a typed record:

```text
assumption_id
statement
scope
introduced_by
evidence
confidence
risk_if_false
observable_signal
invalidation_trigger
fallback
review_by
status
```

Examples:
- "DBOS recovery semantics are adequate for our worker/session lifecycle."
- "PostgreSQL task-DAG traversal remains simple enough."
- "Persistent ChatGPT sessions provide useful continuity for tactical workers."
- "Ctrl+Space operator bridge remains acceptable under real temporary-chat use."
- "Two CPU cores are sufficient for control-plane peak load."

An assumption that has no observable invalidation signal is suspect.

## 9. Architecture Decision Records

Use ADRs only for architecturally significant, hard-to-reverse decisions.

ADRs should record:
- context/problem;
- alternatives;
- decision;
- evidence;
- consequences;
- assumptions;
- fitness functions;
- rollback/replacement path.

Accepted ADRs are immutable; supersede rather than rewrite.

## 10. Architecture fitness functions

Create machine-enforced checks such as:

```text
FF-001 core-domain-has-no-infrastructure-dependencies
FF-002 no-model-inference-grants-authority
FF-003 stale-generation-never-completes-current-work
FF-004 duplicate-effect-event-does-not-duplicate-validated-effect
FF-005 crash-at-every-durable-boundary-recovers
FF-006 semantic-projection-rebuild-is-deterministic
FF-007 waiting-external-does-not-busy-poll
FF-008 control-plane-gpu-usage-zero
FF-009 resource-caps-enforced
FF-010 every-complete-action-has-receipt-and-validation
FF-011 unknown-transition-fails-closed
FF-012 architecture-assumptions-have-invalidation-signals
```

Run fast fitness checks continuously; expensive fault suites at coherent checkpoints.

## 11. CI/release discipline

Do not repeat the current pattern where every tiny mutation pays the full integration-validation cost.

Use tiers:

### per-change fast gate
- schemas;
- lint/type checks;
- pure unit tests;
- architecture dependency checks;
- selected state-machine tests.

Target: short feedback.

### coherent-slice gate
- adapter contracts;
- DB integration;
- stateful/property tests;
- replay/restart tests;
- selected fault injections.

### milestone gate
- full end-to-end real workflow;
- broad fault matrix;
- resource budget;
- architecture fitness;
- security/authority;
- operator/browser integration as applicable.

### release/promotion gate
- full validation;
- migration/recovery rehearsal;
- rollback proof;
- production-readiness review.

## 12. First real implementation slice

The first slice should be intentionally narrow:

1. pure domain types/state machine;
2. `DurableRuntimePort` + DBOS adapter;
3. `StateStorePort` + PostgreSQL adapter;
4. WorkItem + ReasoningProcess + dependency edge;
5. DecisionRecord;
6. CandidateAction + ActionSpec;
7. one read-only GitHub action family;
8. EffectReceipt + postcondition validator;
9. OpenTelemetry trace;
10. crash/replay/fault tests;
11. CPU/RAM/GPU resource measurement;
12. one real Workspace Control task.

No graph database yet.
No vector database.
No microservices.
No general agent framework.
No local LLM.
No GPU dependency.
No autonomous write-heavy action family.

## 13. Freeze criterion

Do not freeze the implementation substrate until the first real workflow proves:

- recovery after injected crashes;
- no duplicated validated effect;
- stale-worker fencing;
- correct wait/wake;
- typed reasoning -> action boundary;
- effect postcondition validation;
- control-plane resource budget;
- debuggable traces;
- context/state usefulness;
- manageable code complexity.

Then perform Architecture Review v0.3 using the trace, incidents, profiler/resource data, and implementation friction as evidence.

The purpose of v0.2 is to make v0.3 informed by reality.
