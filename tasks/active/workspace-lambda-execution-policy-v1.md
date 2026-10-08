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

Run the adversarial/offline reconstruction acceptance for the accepted runtime object 23a47f27bdb6bec63955b901080fc0926cffee8cf081d010195613789bc5bbf4 together with the already-accepted Qwen3.5-4B model object. Reconstruct an ephemeral per-job venv from the trusted runtime wheelhouse with network disabled and exact hash enforcement; verify Python/SOABI/platform, exact vLLM/Torch/TorchVision/TorchCodec identities, native-sampler semantics, multimodal import, and bounded CUDA allocation without model inference. Then exercise corruption/hash failure, replay/stale admission, interrupted reconstruction/cleanup, candidate write denial, process/GPU residue, disk/resource exhaustion behavior, and concurrent isolation as required by the owning acceptance contracts. Do not widen gpu-heavy/dual-GPU authority or alter production/scientific routing.

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
