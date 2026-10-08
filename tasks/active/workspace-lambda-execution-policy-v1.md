<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-lambda-execution-policy-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-lambda-execution-policy-v1
- Title: Workspace Lambda Execution Policy and Model Workload Governance v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Design, implement, and adversarially validate a fail-closed workload admission, trusted model/dependency cache, resource-governance, and execution-evidence layer on top of the accepted Lambda P5 CPU and gpu-small autonomous runner substrate so ChatGPT/GitHub-driven work can safely execute pinned model-scale workloads without granting candidate workflow code the ability to invent capabilities, persist mutable cross-job state, access production/scientific state, or widen host authority.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 42cf6a0bebbc79f4d5657486c7b259bfcc4a5b7a
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 2f8e88ecaa668d5adfc4728c2571e52c002774ab
- Remote verified: true

## Next safe action

Before the full adversarial gate, run one network-isolated timed reconstruction of an ephemeral Python 3.12 venv from trusted runtime object 23a47f27bdb6bec63955b901080fc0926cffee8cf081d010195613789bc5bbf4 using only its local wheelhouse and --require-hashes. Record venv-creation wall time, pip offline-install wall time, resulting venv bytes, exact core package identities, and import smoke with VLLM_USE_FLASHINFER_SAMPLER=0; perform no model inference. Compare measured reconstruction cost against the already-observed ~16-second Lambda gpu-small execution baseline. If pip reconstruction is materially dominant, evaluate a bounded uv clone/COW or hardlink materialization path using the same immutable wheel object before spending effort on the full adversarial acceptance; otherwise keep pip and continue directly to corruption/replay/cleanup/resource/concurrency gates. Do not alter either trusted object, production routing, the daemon, or gpu-heavy authority.

## Remaining work

- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
