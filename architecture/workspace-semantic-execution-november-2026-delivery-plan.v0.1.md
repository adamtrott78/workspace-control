# Workspace Semantic Execution — November 2026 Integrated v0 Delivery Plan

Status: **ACTIVE DELIVERY PROGRAM**

Parent task: `workspace-semantic-execution-migration-v1`

Deadline: **2026-11-30**

Internal red-line: **first real end-to-end vertical slice by 2026-11-23**

Machine-readable acceptance matrix:
`architecture/workspace-semantic-execution-november-2026-acceptance.v0.1.json`

## Objective

By November 30, Workspace Control must be able to accept a substantial high-level task, recursively decompose it, route bounded work to deterministic tools / ChatGPT Instant / subscription Codex as appropriate, execute and recover durably, validate consequential results, synthesize the final result, and account for scarce model usage without paid API fallback or weakened authority.

This is the November Integrated v0 milestone. It is intentionally narrower than migrating every workspace workflow before December. The proving workload is **Research Engine / research-iterate**. Once that workflow proves the substrate, additional research, PADataset, coursework, document, presentation, and infrastructure workflows become incremental migrations rather than core-system invention.

## Four parallel delivery lanes

### Lane A — Reasoning Economy / Codex

Goal:
- Workspace Control has a CPU-only, subscription-only Codex runtime;
- ChatGPT Plus authentication is proven;
- `OPENAI_API_KEY` and paid API fallback are structurally absent;
- Codex execution produces structured trace + economics evidence;
- account usage/rate-limit observations are calibrated conservatively;
- a weekly allowance governor routes/rejects work without purchasing credits.

Current baseline:
- usage collector validated;
- economics ledger validated;
- subscription adapter/trace parsing exists;
- inert Workspace Control bootstrap workflow validated;
- live promotion remains gated on PR #627 lineage.

### Lane B — Semantic orchestration

Goal:
- durable recursive task tree;
- CAS/generation fencing and leases;
- TOO_LARGE -> DECOMPOSE distinct from INTRINSICALLY_DIFFICULT -> ESCALATE;
- event-driven waits;
- deterministic packet compiler;
- executor registry/resource router;
- session broker;
- CandidateAction -> authority-owned ActionSpec boundary;
- EffectReceipt + independent postcondition validation;
- repair/retry/synthesis.

Current baseline:
- production domain kernel already exists;
- runtime/event ledger and fault-injection tests exist;
- DBOS/PostgreSQL adapters exist;
- deterministic router and packet compiler exist;
- Research Engine exact-source shadow canary exists.

Therefore the critical-path task is **integration into one coordinated real workflow**, not rebuilding those components.

### Lane C — Instant Chat execution

Goal:
- semantic executor packets from Lane B feed the production Operator Bridge;
- production action/status transport replaces NoWorkOperatorActionPort and empty workload status;
- persistent ChatGPT Instant sessions behave as executor/session adapters;
- routine operator rhythm remains `Ctrl+Space -> Ctrl+V -> Enter`;
- no manual tab search, prompt editing, SHA/log/state relay, or page-content automation;
- recovery/session rotation returns to durable state.

Current baseline:
- Operator Bridge stages 0-8 validated;
- UT-10, UT-02, UT-03, UT-04 accepted;
- minimize-on-empty and repeat-press protection accepted;
- remaining Stage-10 cases and real-account Stage-12 still gate promotion.

### Lane D — Integrated acceptance

Goal:
- Research Engine / research-iterate proves the complete stack;
- mixed executor routing is observable;
- one induced failure is recovered without manual task-state reconstruction;
- every consequential effect is receipt + validator bound;
- economics evidence measures scarce allowance;
- final review runs the acceptance matrix and records `PROMOTE_V0` or `HOLD/REVISE`.

## End-to-end proving flow

```text
high-level user objective
        |
        v
durable ReasoningProcess / WorkItem
        |
        v
recursive decomposition + dependencies
        |
        v
authority/capability/resource evaluation
        |
        +--> deterministic executor
        +--> ChatGPT Instant session via Operator Bridge
        +--> subscription Codex
        +--> stronger reasoning only when evidence requires
        |
        v
deterministically compiled worker packet
        |
        v
typed result / CandidateAction
        |
        v
authority-owned ActionSpec (when executable)
        |
        v
EffectReceipt
        |
        v
independent postcondition validation
        |
        +--> repair/retry/decompose/escalate
        |
        v
dependency wake + synthesis
        |
        v
final result + economics/provenance receipt
```

No model owns this loop. Chat sessions are caches. Durable state is the recovery source.

## Critical calendar

### Nov 15-17 — integration freeze + blocker clearing
Required exit:
- this plan + machine acceptance matrix are durable;
- current code reality is mapped to PASS/PARTIAL/PENDING/BLOCKED;
- PR #627/Codex promotion path is resolved or explicitly tracked as the Codex critical blocker;
- Operator Bridge production action/status transport contract is frozen;
- Research Engine coordinated vertical-slice implementation target is concrete.

### Nov 18-20 — orchestration integration spine
Required exit:
- recursive task-tree semantics run through the production RuntimeCoordinator;
- session broker exists;
- deterministic packet compiler is used by the coordinated path;
- executor registry/router produces durable RoutingDecision records;
- event/wait + validator services are integrated rather than isolated tests.

### Nov 18-21 — Codex live executor, parallel
Required exit:
- approved Workspace Control runtime route;
- ChatGPT Plus auth proven;
- subscription-only execution wrapper operational;
- JSONL traces + before/after account telemetry flow into economics records.

### Nov 18-22 — Instant production binding, parallel
Required exit:
- real backend action/status transport feeds the existing bridge;
- remaining short Stage-10 judgment/recovery/no-work gates complete;
- fake-worker tests remain green.

### Nov 21-23 — FIRST REAL VERTICAL SLICE
Required exit:
- Research Engine / research-iterate completes through the new orchestration path;
- at least one real routing decision and independently validated low-consequence effect occur;
- no manual control-plane state reconstruction is required.

**If this gate is not reached by Nov 23, secondary architecture and feature work stops until it is reached.**

### Nov 24-26 — Reasoning Economy + recursive mixed execution
Required exit:
- multi-level TOO_LARGE decomposition works;
- mixed deterministic / Instant / Codex routing works;
- controlled usage calibration exists;
- weekly burn governor is operational;
- cheaper executor promotion remains quality-gated.

### Nov 25-27 — reliability campaign
Required exit:
- stale generation, duplicate/delayed/out-of-order events, executor loss, validator timeout, database/runtime interruption, and effect-boundary crashes are injected against the integrated stack;
- no duplicate validated effect and no stale completion.

### Nov 27-28 — real-account calibration
Required exit:
- remaining Operator Bridge Stage-10 acceptance is complete;
- bounded Stage-12 real-account calibration passes;
- no ChatGPT DOM/content scraping or synthetic send boundary is introduced.

### Nov 28-29 — performance + soak
Required exit:
- authoritative UX-09 target performance passes;
- representative-work collision/soak passes;
- control plane stays GPU-blind and within resource fitness targets;
- allowance burn is measured.

### Nov 30 — acceptance freeze
Required exit:
- every mandatory requirement in the machine-readable matrix is PASS;
- no new scope-expanding features are admitted;
- integrated review records explicit `PROMOTE_V0`, otherwise the program records `HOLD` or `REVISE`.

## Requirements governance

The JSON acceptance matrix is the authoritative November completion checklist.

Rule:

> Every implementation item must close or materially advance at least one ORCH, SAFE, CODEX, ECON, INST, REL, E2E, or PROD requirement.

If a proposed task cannot identify its requirement ID and it does not remove a demonstrated blocker, it is outside the November critical path.

Existing evidence may mark a requirement PARTIAL or PASS only when the evidence actually proves that requirement. Component implementation alone is not equivalent to integrated acceptance.

## Non-blocking work for November

These are explicitly not required to declare Integrated v0 complete:
- live institutional H100/Harmony deployment;
- migration of every PADataset/course/document/presentation workflow;
- choosing/finalizing a graph database or vector database;
- replacing the accepted GitRunner/controller;
- proving broad Instant-vs-frontier capability equivalence beyond the routing quality floors needed by the v0 workflows.

The architecture must support those future extensions without kernel redesign, but November does not wait for them.

## Promotion rule

November Integrated v0 is **not complete** because the architecture is sophisticated or because individual components pass tests.

It is complete only when:
1. the full machine-readable acceptance matrix is PASS;
2. the Research Engine proving workflow succeeds through the integrated stack;
3. failure/recovery evidence is recorded;
4. scarce-allowance economics are recorded;
5. security/authority/provenance gates remain intact;
6. the integrated production-readiness review records `PROMOTE_V0`.
