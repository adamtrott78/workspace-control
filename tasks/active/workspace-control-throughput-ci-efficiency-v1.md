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
- Remote checkpoint: da5653093799324ba90f45364ec8d6ce752140d2
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 7a26e648ec409c96a3f9b7c8620f566658700894
- Remote verified: true

## Next safe action

Start from https://github.com/adamtrott78/workspace-control and the normal root route. The current canonical base for this Wave-3 design is main@da5653093799324ba90f45364ec8d6ce752140d2. Complete and validate field_efficiency_wave3_design on branch throughput-efficiency-wave3-design-v1. Do not start the final cross-repository rollout task and do not mutate research-engine from this capsule. Preserve the active research-engine Qwen task's exact durable next_safe_action; use its natural retries only as field evidence to calibrate C2a backend/toolchain resolution, C2b engine boot, C3 same-modality canary, persistent compile-cache reuse, subprocess failure envelopes, resumable stage receipts, structured process identity, bounded diagnosis, and control-cycle latency. Keep Qwen/vLLM/FlashInfer/package/model/scientific specifics project-local. After FULL_INTEGRATION validation and promotion, synchronize the task checkpoint and move to Wave-3 field validation.

## Remaining work

- Validate and promote the Wave-3 design without creating the final cross-repository rollout task.
- Continue using the active research-engine Qwen task as a natural field workload through its own authority; do not mutate research-engine from this capsule.
- Calibrate C2a backend/toolchain resolution against the demonstrated FlashInfer/nvcc failure and any subsequent natural backend selection evidence.
- Calibrate C2b real engine-boot certification and record cold versus persistent compile/JIT cache behavior on required natural retries.
- Define the minimum C3 same-modality synthetic canary that proves request-path viability without consuming scientific/domain inputs.
- Prototype generic failure-envelope fields that preserve first causal child/JIT/subprocess errors while keeping full logs referenced rather than inlined.
- Measure interruption recovery and root-cause-to-durable-correction control-cycle latency; treat repeated opaque reasoning/recovery cycles as first-class waste.
- Measure append-only Git mutation with fewer dedicated rereads while preserving non-fast-forward safety and hard verification at semantic boundaries.
- Continue task JSON→Markdown semantic-transaction work; authoritative JSON must remain the single edit surface.
- Freeze Wave 3 only after the architecture survives additional natural runtime evidence without substantive shared redesign; only then plan broad rollout.

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
