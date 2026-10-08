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

Implement and validate the researched steady-state runtime-sharing design instead of further installer tuning. Build one expanded Qwen runtime from the already-trusted 196-wheel object under root authority, at a stable execution path, using Python 3.12 and the accepted exact hashes. Verify exact package/runtime identity, harden the expanded tree root-owned/read-only, and expose it to a candidate job only through a private mount namespace as a read-only runtime. Redirect HOME/TMPDIR/XDG/Python bytecode/Torch/vLLM caches to disposable job-local writable paths. Run a no-model-inference compatibility canary proving exact imports plus bounded CUDA allocation from this direct read-only runtime. If any component requires writes beneath the runtime path, add a per-job OverlayFS upper/work layer over the immutable lower and repeat the canary; otherwise prefer the simpler direct read-only mount. Do not use hardlink or symlink materialization as the primary design, do not alter host filesystem layout, and do not widen gpu-heavy or candidate privileges.

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
