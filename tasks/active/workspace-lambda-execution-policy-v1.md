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

Using the accepted bundle at ~/adamArchives/Adam/workspace-control-tmp/qwen35-runtime-bundle-build-20261008T022554Z/bundle, extract a compact license-review record only for cuda-toolkit, humming-kernels, openai-harmony, quack-kernels, and torchcodec: exact wheel filename/version/SHA-256 from bundle-manifest.json; root METADATA Home-page/Project-URL fields; and names/SHA-256 of bundled LICENSE/COPYING/NOTICE files without modifying the bundle. Use those exact identities to verify authoritative upstream license/usage terms. If all five are compatible with this internal research/CI use, record a trusted package-set license review and proceed to root trusted-cache acquisition/promotion of the already-verified bundle. Do not rebuild the bundle, reconstruct the full venv, run inference, alter the accepted model object, control the daemon, or widen model-eval/gpu-heavy authority.

## Remaining work

- Promote/build and pin the exact qwen35-vllm-cu129-image-native-sampler-v3 runtime/dependency object independently of model weights, suitable for read-only offline model-eval.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- Runtime bundle materialization is accepted, but root promotion remains blocked on the package-set license/usage review. Only five exact wheel artifacts lack declared license metadata: cuda-toolkit, humming-kernels, openai-harmony, quack-kernels, torchcodec. Resolve their exact versions/upstream/license evidence from the built wheel contents and authoritative upstream sources, then complete the trusted review before promotion.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
