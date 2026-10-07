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
- Remote checkpoint: 66361693ad2f8d0a345d420dabccbbd6042f5c59
- Remote verified: true

## Next safe action

On Lambda, promote the already-prefetched Qwen/Qwen3.5-4B snapshot from /home/atrott/adamArchives/Adam/.research-engine/residual-models/qwen3.5-4b/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a using the installed root-owned trusted cache manager. Before acquisition, require the source to contain exactly 14 regular files, total materialized bytes 9342907469, no symlinks, and exact primary weight SHA-256 values 26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61 and cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188, matching research-engine residual-model-prefetch-pass.v1.json. Use a descriptor bound to repo Qwen/Qwen3.5-4B, immutable revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a, Apache-2.0, safetensors, unsafe_deserialization=false, custom_code=false, recipe lambda-ci-trusted-cache-v1, implementation_sha 42cf6a0bebbc79f4d5657486c7b259bfcc4a5b7a. Acquire into root quarantine, promote atomically, require offline verify PASS as ci-research-engine, and record the resulting content-addressed object id plus full promotion receipt. Do not enable model-eval, perform inference, download alternate weights, or mutate production/scientific state.

## Remaining work

- Promote and offline-verify the already-prefetched exact Qwen/Qwen3.5-4B snapshot at revision 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a through the trusted cache manager, preserving its existing prefetch provenance and validating file count/materialized bytes plus both primary weight digests.
- Promote/build and pin the exact qwen35-vllm-cu129-image-native-sampler-v3 runtime/dependency object independently of model weights, suitable for read-only offline model-eval.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- None. The canary promotion/consumer/cleanup gate is fully accepted; exact Qwen snapshot promotion may proceed while model-eval remains disabled.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
