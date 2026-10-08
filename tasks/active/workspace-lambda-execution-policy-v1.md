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

## Current stage

trusted_cache_promotion_and_provenance

## Next safe action

Design and build a content-addressed Qwen runtime dependency bundle rather than promoting the raw venv. Use the exact 196-line freeze (SHA-256 198d90f866d032ea8f747dd9d28a1fe5f5ef18c02e5eb64b850124e77a2744d0) plus the owning runtime contract to construct a symlink-free trusted package payload containing exact wheel/source artifacts, hashes, indexes/source URLs, Python ABI/platform constraints, native-sampler environment semantics, and a deterministic offline reconstruction manifest. The bundle must be consumable with network disabled into an ephemeral per-job venv, after which the reconstructed environment must reproduce the exact vLLM/Torch/TorchVision/TorchCodec identities and prior multimodal/CUDA smoke without model inference. Do not mutate or promote the live venv, do not alter the accepted model object, do not enable model-eval, and do not widen gpu-small or gpu-heavy authority.

## Remaining work

- Promote/build and pin the exact qwen35-vllm-cu129-image-native-sampler-v3 runtime/dependency object independently of model weights, suitable for read-only offline model-eval.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- Raw qwen3.5 venv promotion is denied by observed structure: symlinks, cache-v1-forbidden suffixes, secret-name/marker hits, absolute shebangs, and extensive absolute-prefix coupling. The next design must promote immutable package/dependency inputs and an exact reconstruction manifest rather than the live venv tree.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
