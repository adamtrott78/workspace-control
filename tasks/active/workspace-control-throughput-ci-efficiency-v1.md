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
- Remote checkpoint: e25ba2c4e602a525b213450bf8a9c2f5014321e0
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 7a26e648ec409c96a3f9b7c8620f566658700894
- Remote verified: true

## Next safe action

Start from https://github.com/adamtrott78/workspace-control and the normal root route. Wave-3 execution-certification and control-cycle architecture is canonical on main@e25ba2c4e602a525b213450bf8a9c2f5014321e0. Continue field_efficiency_wave3_validation; do not start the final cross-repository rollout task and do not mutate research-engine from this capsule. Preserve the active research-engine Qwen task's exact durable next_safe_action and use only its natural retries as field evidence. Prioritize: (1) C2a backend/toolchain resolution and explicit backend identity, (2) C2b real engine boot plus persistent compile/JIT cache cold-vs-reuse measurement, (3) a minimal C3 same-modality synthetic canary before reusable runtime-ready certification, (4) structured child/JIT/subprocess failure envelopes, (5) idempotent interruption recovery, and (6) root-cause-to-durable-correction/control-cycle latency. Keep Qwen/vLLM/FlashInfer/package/model/scientific specifics project-local. Freeze Wave 3 only when its exit criteria survive additional natural evidence without substantive shared redesign.

## Remaining work

- Use natural owning-project work, beginning with the active research-engine Qwen task, to validate Wave-3 mechanisms without replacing or weakening the owning task's next_safe_action.
- Measure C2a execution-backend/toolchain resolution against dynamic optional backend requirements; backend choice must be explicit execution identity, not silent fallback.
- Measure C2b real engine boot and persistent compile/JIT cache behavior on required natural retries; preserve partial-init resource values as diagnostic only.
- Define and validate a minimal C3 same-modality synthetic canary; reusable runtime-ready certification must not be written before C3 passes.
- Capture the first causal child/JIT/subprocess error in a compact failure envelope so routine diagnosis does not require full console logs.
- Demonstrate interruption recovery from durable operation/stage receipts with no repeat of already valid expensive stages.
- Measure root-cause-to-durable-correction and total control-cycle latency, including avoidable assistant/recovery cycles when observable.
- Continue append-only Git mutation measurement with direct-descendant force=false updates and verification coalesced at semantic boundaries; use conservative CAS/read paths outside that invariant.
- Implement the generic task-sync helper only after Wave-3 field evidence stops changing the required receipt/task fields.
- Do not create the final cross-repository rollout task until Wave-3 exit criteria are met and new findings are predominantly project-specific.

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
