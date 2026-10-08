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

Benchmark uv 0.12.23 copy-mode materialization against the same trusted runtime object. Extract the trusted uv archive only into ephemeral candidate-owned space. Run inside a network-isolated namespace with exact Python 3.12, --offline, --no-index, --no-python-downloads, --only-binary=:all:, --require-hashes, --find-links pointing only at the trusted wheelhouse, and --link-mode copy. Use a fresh temporary UV_CACHE_DIR. First create/install into a cold fresh venv and time venv creation plus uv install; then create a second fresh venv while reusing the now-warm same temporary uv cache and time the warm copy-mode install separately. Re-run exact 196-package identity, Qwen3.5 multimodal import, native-sampler environment, bounded 256 MiB CUDA allocation, and cleanup without model inference. The shared benchmark cache is temporary only; do not yet treat a candidate-writable uv cache as an accepted cross-job cache. If the warm result materially beats the 84.460038 s pip baseline, design the final persistent cache as a root-populated/read-only trusted cache object before adversarial acceptance.

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
