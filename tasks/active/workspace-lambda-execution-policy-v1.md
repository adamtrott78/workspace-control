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
- Remote checkpoint: 893b38da5ec4eca0146b236579f16f28f04f3e7d
- Remote verified: true

## Next safe action

On Lambda, rerun the qwen35-vllm-cu129-image-native-sampler-v3 wheel-only dependency-bundle materialization using exact research-engine commit 893b38da5ec4eca0146b236579f16f28f04f3e7d. Preserve the certified live runtime read-only; write only under ~/adamArchives/Adam/workspace-control-tmp/ with output-local PIP_CACHE_DIR; require the exact 196-line freeze SHA-256 198d90f866d032ea8f747dd9d28a1fe5f5ef18c02e5eb64b850124e77a2744d0; permit only wheel downloads from the declared PyPI/PyTorch indexes plus the exact certified vLLM upstream release URL/hash; require builder and independent verify PASS. Do not promote yet. Return bundle-manifest.json and compact console evidence so the package-level license inventory, artifact count/bytes, vLLM hash, and any missing/unsupported artifact can be reviewed before root promotion. Do not reconstruct the full venv yet, run inference, alter the accepted model object, stop/start the production daemon, or widen model-eval/gpu-heavy authority.

## Remaining work

- Promote/build and pin the exact qwen35-vllm-cu129-image-native-sampler-v3 runtime/dependency object independently of model weights, suitable for read-only offline model-eval.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- No persistent runtime object exists yet. The builder now correctly recognizes the exact certified local vLLM freeze provenance. Re-run the same bounded Lambda bundle materialization from research-engine@893b38da5ec4eca0146b236579f16f28f04f3e7d, inspect the artifact/license manifest, complete the required trusted package-set license/usage review, and only then perform root trusted-cache acquisition/promotion.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
