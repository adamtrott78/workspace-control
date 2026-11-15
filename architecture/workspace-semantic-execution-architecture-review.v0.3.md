# Workspace Semantic Execution — Architecture Review v0.3

Status: **EVIDENCE-BASED PROVISIONAL ACCEPTANCE / ADVANCE TO INTEGRATED VERTICAL SLICE**

Parent task: `workspace-semantic-execution-migration-v1`

Backend task: `workspace-semantic-execution-backend-v1`

Date: 2026-11-15

Reviewed implementation head: `fa29ea7894c64d32795141661ceaa31e84a6a9ac`

Primary validation:
- Workspace Control Validation #2787 — SUCCESS
- Semantic Execution Validation #85 / run `43728753015` / job `132856334315` — SUCCESS

## 1. Decision

**Retain DBOS 3.5.0 + PostgreSQL 17 as the provisional Integrated-v0 durability/state substrate behind the existing ports.**

Do not architecture-freeze DBOS or PostgreSQL as permanent dependencies.

Do not spike Restate or Temporal before the first coordinated Research Engine vertical slice unless new evidence invalidates the current substrate assumptions.

The implementation has now supplied the evidence v0.2 required before advancing:
- pure domain kernel exists;
- infrastructure is behind ports;
- PostgreSQL CAS/event durability survives adapter recreation;
- DBOS bounded work recovers after abrupt process death;
- semantic external waits remain separate from DBOS blocking receive semantics;
- exact read-only external effect + independent postcondition validation works;
- real Research Engine source/workflow shape projects through the generic kernel;
- stale generations and duplicate/conflicting effects fail closed;
- explicit fault suite passes;
- control plane is GPU-blind;
- current resource probe is comfortably inside memory/burst targets.

The next architecture question is no longer “can these pieces work separately?” It is:

> Can the pieces execute one coordinated real Research Engine workflow slice through routing, deterministic packet compilation, authority, effect, validation, durable state, recovery, and synthesis without introducing substrate-specific domain logic?

That becomes the next bounded implementation slice.

## 2. Evidence reviewed

### Domain and authority

Validated behavior includes:
- pure domain package with no DBOS/PostgreSQL/GitHub/browser/model-provider/GPU dependency;
- generation fencing;
- single current lease semantics;
- dependency readiness/fan-in;
- external/dependency wait preservation across recovery;
- fail-closed unknown transitions;
- CandidateAction cannot self-authorize;
- exact process/generation/action/target authority binding;
- ActionSpec cannot complete from tool success alone.

### Runtime and fault behavior

Semantic Execution Validation #85 ran the explicit backend suite and passed **67 tests** covering:
- crash/death after claim;
- stale lease/generation rejection;
- crash after effect before checkpoint;
- exactly-once receipt retention;
- conflicting duplicate effect rejection;
- duplicate external event idempotency;
- delayed wrong-event isolation;
- out-of-order event-before-wait reconciliation;
- restart while waiting;
- validator timeout/recovery;
- deterministic serialization;
- state-store CAS conflict rejection;
- deterministic projection;
- executor/router/packet invariants.

### DBOS/PostgreSQL

The same run passed **7 integration tests** covering:
- pinned DBOS `3.5.0`;
- pinned psycopg `3.3.9`;
- PostgreSQL 17;
- state-store CAS after adapter recreation;
- immutable event evidence after restart;
- semantic wait/restart/resume without model polling;
- DBOS work-id idempotency/conflicting-input rejection;
- abrupt `os._exit` process death followed by successful DBOS workflow recovery in a fresh process;
- explicit proof that semantic external waits do not call `DBOS.recv`.

No custom replay/event-sourcing engine was required.

### Real Research Engine canary

The frozen source:
- repository: `adamtrott78/research-engine`
- commit: `1031861c03b2af8cff5f6461f7469f0eed1e79e43` is **not** the reviewed canary identity; the backend task uses exact reviewed source `1031861c03b2af8cff5cf72939bbbc83a95e65a4`;
- path: `src/research_engine/orchestration.py`
- blob: `0d051fa50960708e0e773f6871c7e924c5796394`

was represented by the generic production kernel without a Research-Engine-specific state-machine branch.

The read-only effect generated an EffectReceipt and the independent validator reread the exact immutable source before allowing completion.

Research Engine itself remained unmodified.

## 3. Resource verdict

The Semantic Execution #85 resource probe reported:

```text
CUDA_VISIBLE_DEVICES=""
max_rss_mib=18.0
observed_cpu_cores=0.9999200264
wall_seconds=41.7007
iterations=1000
```

Current provisional fitness targets:
- GPU visible devices: 0 — **PASS**
- GPU VRAM: 0 — **PASS by GPU-blind execution contract**
- application RSS <= 1024 MiB — **PASS with large margin**
- burst CPU <= 2 logical cores — **PASS**
- steady CPU < 1 core — synthetic probe measured just under one core while intentionally executing 1000 iterations; this is **not yet representative idle/real-workflow steady-state evidence**.

Verdict:
- no resource reason to reject the modular-monolith/DBOS/PostgreSQL direction;
- keep the real-workflow resource measurement requirement open;
- production/soak acceptance still requires workload-specific CPU/RSS evidence.

## 4. Assumption review

### A-001 DBOS + PostgreSQL first substrate

Status: **PROVISIONALLY SUPPORTED — ADVANCE**

No two important semantics currently require bespoke substrate workarounds.

Observed semantics covered by existing ports:
- durable bounded work;
- crash recovery;
- CAS current state;
- immutable external event evidence;
- idempotent work identity;
- explicit external waits.

Restate trigger is **not reached**.

Temporal trigger is **not reached**.

Re-open substrate comparison if the coordinated Research Engine slice exposes:
- custom replay machinery;
- awkward long suspension/callback semantics;
- versioning/migration limitations;
- substrate-specific leakage into the domain/application layer;
- operational/resource cost outside fitness budgets.

### A-002 modular monolith

Status: **SUPPORTED**

No current component requires independent service scaling. External executors and Operator Bridge are already isolated behind boundaries.

### A-003 Git is not hot runtime state

Status: **SUPPORTED**

Current StateStore/EventLedger design successfully moves high-frequency runtime coordination out of Git while retaining Git for source/task/provenance checkpoints.

### A-004 semantic projection is derived

Status: **SUPPORTED**

Deterministic projection is adequate for current bounded queries. No graph-database trigger is reached.

### A-005 Instant default bounded reasoning

Status: **ONLINE CALIBRATION**

No architecture change. Routing quality remains subject to validator evidence and Reasoning Economy policy.

### A-006 persistent chat is a cache

Status: **SUPPORTED PROVISIONAL**

The deterministic packet compiler proves state can be reconstructed independent of chat transcript. Production session-broker behavior remains to be implemented/accepted.

### A-007 zero-GPU modest control plane

Status: **PARTIALLY PROVEN**

GPU blindness and memory targets pass. Real integrated-workflow steady resource evidence remains open.

### A-008 small explicit agent loop

Status: **SUPPORTED**

No general agent framework is needed for current kernel/runtime/application semantics.

## 5. Fitness-function verdict

- FF-001 core-domain-has-no-infrastructure-dependencies — **PASS**
- FF-002 model-inference-cannot-grant-authority — **PASS**
- FF-003 stale-generation-cannot-complete-current-work — **PASS**
- FF-004 duplicate-effect-event-cannot-duplicate-validated-effect — **PASS**
- FF-005 crash-at-durable-boundaries-recovers — **PARTIAL/PASS for tested boundaries; keep integrated-workflow fault injection open**
- FF-006 semantic-projection-rebuild-is-deterministic — **PASS**
- FF-007 waiting-external-does-not-busy-poll — **PASS**
- FF-008 control-plane-gpu-usage-zero — **PASS in validation environment**
- FF-009 control-plane-resource-budget — **PARTIAL/PASS for synthetic probe; real workflow still required**
- FF-010 complete-action-has-receipt-and-validation — **PASS**
- FF-011 unknown-transition-fails-closed — **PASS**
- FF-012 material-assumptions-have-invalidation-signals — **PASS**

## 6. Architecture changes since v0.2

No foundational reversal is required.

The main change is execution priority:

**Before v0.3:** prove isolated substrate/kernel/read-only pieces.

**After v0.3:** stop expanding isolated primitives and assemble the first coordinated real vertical slice.

The first slice MUST reuse existing domain/runtime/router/packet/authority/effect/validator code. It MUST NOT fork parallel orchestration semantics merely to make the demo work.

## 7. Next bounded implementation slice

Name: **Research Engine coordinated read-only vertical slice v1**

Required flow:

1. initialize/load a durable ReasoningProcess;
2. represent one exact Research Engine objective/work item;
3. compute an ExecutionRequirement;
4. route through the generic ExecutorRegistry;
5. deterministically compile the worker packet from typed state;
6. produce a CandidateAction;
7. obtain an exact preloaded/read-only AuthorityDecision;
8. compile ActionSpec through the production authority boundary;
9. claim/start the process through RuntimeCoordinator;
10. execute one exact immutable Research Engine repository read;
11. record EffectReceipt;
12. propose terminal state;
13. independently reread/validate the postcondition;
14. record ValidationResult and reach COMPLETED only on validator PASS;
15. emit a structured vertical-slice result containing routing, packet digest, authority binding, receipt, validation evidence, final process state, and telemetry refs.

Required negative tests:
- unknown authority -> no executable ActionSpec;
- stale generation after routing/packet compilation -> no effect;
- unavailable/incompatible executor -> no execution;
- changed source bytes -> validation failure / repair-ready state;
- duplicate exact effect -> no duplicate validated effect;
- deterministic rerun of packet compilation -> same packet hash.

Non-goals:
- no Research Engine mutation;
- no write-capable GitHub action;
- no browser/Instant invocation yet;
- no Codex live invocation yet;
- no new distributed service;
- no new database.

Exit gate:
- coordinated slice passes Semantic Execution Validation;
- architecture ports remain clean;
- no Research Engine write occurs;
- evidence maps directly to November requirements ORCH-01/04/05/06/07, SAFE-01/02, REL-01, and E2E-01 precursor.

## 8. Write-capable authority decision

**Do not add write authority yet.**

v0.3 supports advancing from isolated read-only canary to coordinated read-only vertical-slice orchestration.

A bounded low-consequence write-capable slice may be proposed only after the coordinated read-only slice demonstrates:
- correct router/packet/authority/effect/validator composition;
- no substrate leakage;
- stale-generation and duplicate-effect safety;
- deterministic recovery;
- acceptable resource trace.

That future write-capable slice requires its own exact authority surface and postcondition contract.

## 9. Final v0.3 verdict

```text
SUBSTRATE_DECISION=RETAIN_PROVISIONALLY
DBOS_3_5_0=RETAIN_BEHIND_PORT
POSTGRESQL_17=RETAIN_BEHIND_PORT
RESTATE_SPIKE=NOT_TRIGGERED
TEMPORAL_SPIKE=NOT_TRIGGERED
GRAPH_DATABASE=NOT_TRIGGERED
CONTROL_PLANE_GPU=FORBIDDEN
WRITE_AUTHORITY_WIDENING=NOT_AUTHORIZED
NEXT_SLICE=RESEARCH_ENGINE_COORDINATED_READ_ONLY_VERTICAL_SLICE_V1
```

This is not an architecture freeze.

It is authorization-by-evidence to advance to the first coordinated real workflow slice while preserving the existing rollback and substrate-replacement boundaries.
