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

Benchmark a bounded uv-based offline materializer against the same trusted runtime object before the full adversarial gate. First inspect whether an accepted uv binary already exists on Lambda and record its exact version/path/digest plus the filesystem types for trusted cache and ephemeral job workspace. If uv is absent, stop and design a separately pinned/verified uv tool acquisition rather than curl|sh or candidate-controlled installation. If uv is present, use an isolated temporary uv cache populated only from the trusted wheelhouse, no network, no Python downloads, no index, no source builds, and exact hash enforcement. Measure cold cache population separately from warm per-job materialization. Prefer clone/COW only if the filesystem supports it and the resulting job environment is inode-distinct from the immutable cache; otherwise benchmark copy. Do not use symlink mode. Hardlink mode may be measured only as a non-authoritative comparison unless write-denial/inode-isolation proves it cannot mutate the shared cache. Re-run the exact 196-package identity, multimodal import, bounded CUDA allocation, and cleanup checks without model inference. Use the measured result to select the steady-state materializer before corruption/replay/cleanup/resource/concurrency acceptance.

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
