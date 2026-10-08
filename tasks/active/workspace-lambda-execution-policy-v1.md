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

On Lambda, rerun the qwen35-vllm-cu129-image-native-sampler-v3 wheel-only dependency-bundle materialization using exact research-engine commit 2f8e88ecaa668d5adfc4728c2571e52c002774ab and builder blob 6902282fe1339622931c799df281fb8b8ce63673. Preserve the certified live runtime read-only; write only under ~/adamArchives/Adam/workspace-control-tmp/ with output-local PIP_CACHE_DIR; require exact freeze SHA-256 198d90f866d032ea8f747dd9d28a1fe5f5ef18c02e5eb64b850124e77a2744d0; permit only declared wheel sources plus exact certified vLLM upstream URL/hash; require builder and independent verify PASS. Do not promote yet. Return only compact console evidence plus bundle-manifest.json (or build-summary.json if PASS); do not send routine per-package download lines unless a failure names a package whose surrounding output is needed.

## Remaining work

- Promote/build and pin the exact qwen35-vllm-cu129-image-native-sampler-v3 runtime/dependency object independently of model weights, suitable for read-only offline model-eval.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- No persistent runtime object exists yet. The wheel metadata parser now handles nested vendored dist-info correctly. Re-run the bounded Lambda bundle materialization from research-engine@2f8e88ecaa668d5adfc4728c2571e52c002774ab, inspect the resulting manifest/license inventory, complete trusted package-set license/usage review, then perform root promotion.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
