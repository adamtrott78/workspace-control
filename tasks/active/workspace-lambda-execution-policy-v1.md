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

Promote the already-built, independently verified Qwen runtime bundle at ~/adamArchives/Adam/workspace-control-tmp/qwen35-runtime-bundle-build-20261008T022554Z/bundle through the installed lambda-ci-trusted-cache-v1 manager as artifact_kind=runtime for project research-engine. Bind the descriptor to runtime contract qwen35-vllm-cu129-image-native-sampler-v3, immutable bundle manifest identity f67ff9a26690c55930232c915e59e826e3cca2dd89012de9e35a852032b38f74, trusted license review policies/lambda-ci-qwen35-runtime-license-review.v1.json, serialization format python-wheelhouse-offline-v1 with unsafe_deserialization=false/custom_code=false, and installed manager implementation SHA 42cf6a0bebbc79f4d5657486c7b259bfcc4a5b7a. Root acquire into quarantine, verify exact 196-wheel payload identity, promote atomically, independently verify as ci-research-engine/read-only/offline-complete, prove candidate writes denied, and preserve the source bundle unchanged. Do not rebuild the bundle, reconstruct the venv, run inference, alter the accepted model object, control the daemon, or widen model-eval/gpu-heavy authority.

## Remaining work

- Promote/build and pin the exact qwen35-vllm-cu129-image-native-sampler-v3 runtime/dependency object independently of model weights, suitable for read-only offline model-eval.
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
