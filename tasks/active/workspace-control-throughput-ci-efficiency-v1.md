<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-control-throughput-ci-efficiency-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-control-throughput-ci-efficiency-v1
- Title: Workspace Control Throughput & CI Efficiency v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Measure and remove avoidable latency from ChatGPT/GitHub/workspace-control execution loops while preserving provenance, fail-closed mutation semantics, durable recovery, and implementation quality. Optimize both orchestration overhead and CI topology so routine low-risk changes do not pay the same synchronous validation cost as high-risk production changes, without weakening the full safety net.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 54758e227ed452ac0d7598889158ddd04e254a4c
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 7a26e648ec409c96a3f9b7c8620f566658700894
- Remote verified: true

## Next safe action

Start from https://github.com/adamtrott78/workspace-control and the normal root route. Wave-3 shared runtime-certification/recovery primitives are implemented and FULL_INTEGRATION validated on main@54758e227ed452ac0d7598889158ddd04e254a4c through scripts/runtime_certification.py plus runtime certification/operation/failure-envelope schemas and focused tests. Continue field_efficiency_wave3_validation without rerunning workloads solely for telemetry and without weakening any owning project's scientific or production next_safe_action. On the next natural heavyweight-runtime work, adopt the shared primitives opportunistically and collect only the remaining evidence: (1) verified R2 compile/JIT cache cold-vs-reuse timing under unchanged execution identity; (2) one actual C3 same-modality synthetic canary that shares the already-booted engine with subsequent domain work; (3) compact operation/certification receipts and any structured causal failure envelope; and (4) control-cycle/recovery measurements when naturally observable. Keep project-specific model/backend/package/scientific facts project-local. If R2 and C3 pass without exposing a new shared mechanism, freeze Wave 3 and prepare the cross-repository rollout task.

## Remaining work

- Use the merged shared implementation at workspace-control main@54758e227ed452ac0d7598889158ddd04e254a4c for future heavyweight-runtime work; owning projects may adopt it incrementally without changing their scientific/production authority.
- On the next natural second engine boot under an unchanged execution identity, measure R2 persistent compile/JIT cache reuse against the cold-v3 baseline (18.17 s compile, 48.84 s profiling/warmup, 117.6484 s total model initialization). Do not rerun solely for telemetry.
- Execute one owning-project C3 same-modality synthetic canary when naturally authorized. It must be cheap, non-scientific, and share the already-booted engine with subsequent domain work rather than triggering a second model boot.
- Return compact operation/certification receipts and failure envelopes by default; retrieve full logs only when the compact evidence does not identify the first causal failure.
- Continue measuring control-cycle latency and interruption recovery opportunistically, especially root-cause-to-durable-correction delay and duplicate-stage work avoided.
- Implement the generic task-sync helper after Wave-3 receipt/task fields remain stable through the next natural adoption.
- Freeze Wave 3 and open the final cross-repository rollout task once R2 reuse and one real C3 adoption pass without revealing a new shared control-plane mechanism.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-control-throughput-ci-efficiency-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
