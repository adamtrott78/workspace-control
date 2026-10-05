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
- Remote checkpoint: 0e726530c0869dfb126958867cf0b7144e4e28de
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 7a26e648ec409c96a3f9b7c8620f566658700894
- Remote verified: true

## Next safe action

Start from https://github.com/adamtrott78/workspace-control and the normal root route. Wave-2 efficiency architecture is canonical on main@0e726530c0869dfb126958867cf0b7144e4e28de. Continue field_efficiency_wave2_validation without starting the final cross-repository rollout task. Do not mutate research-engine from this capsule. Use the active research-engine Qwen task as the natural field workload and preserve its exact durable next_safe_action; through that task's own authority, measure/test layered host/build plus exact execution-path preflight, exact runtime/wheel reuse, compact early-failure receipts, content-addressed deterministic render reuse, Git mutation/write-call behavior, and task-handoff synchronization overhead. Keep package/model/cache specifics project-local and return measured evidence before promoting further shared implementation.

## Remaining work

- Use the current research-engine Qwen task as the primary Wave-2 field workload without replacing or weakening its durable next_safe_action.
- Measure layered runtime preflight: host/build selection before heavyweight install, then exact vLLM multimodal import/native-library/CUDA smoke validation before deterministic render or inference.
- Measure exact runtime/wheel cache reuse with a canonical identity plus verified wheel hashes and a matching execution-path smoke receipt.
- Implement/measure compact failure receipts for early benchmark failure and compare receipt size plus diagnosis tool calls against full console-log handoff.
- Measure content-addressed deterministic render reuse using complete PDF SHA/page/bbox/DPI/renderer identity; incomplete identity must fail closed to rerender.
- Design the follow-up task-sync implementation so authoritative task JSON and derived Markdown are one semantic mutation transaction instead of two independently managed surfaces.
- Continue measuring connector write capability and file/write/commit counts; the advertised expected_sha lease remains broken on the current connector despite appearing in its schema.
- Continue opportunistic TARGETED_PR measurement on real changes; do not manufacture churn only to obtain a benchmark.
- Do not create the final repo-by-repo efficiency rollout task until Wave-2 field validation stops uncovering substantive shared architecture changes.

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
