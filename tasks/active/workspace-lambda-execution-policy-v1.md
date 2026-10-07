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

On Lambda, perform a read-only classification of /home/atrott/adamArchives/Adam/.research-engine/residual-models/qwen3.5-4b/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a using the exact owning research-engine prefetch semantics: payload files are regular files whose path relative to the model root has no `.cache` component. Print raw total file/bytes, `.cache` file/bytes, and payload file/bytes. Require payload exactly 14 files and 9342907469 bytes and re-verify primary weight SHA-256 values 26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61 and cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188. If any payload identity differs, stop fail-closed and print the relative payload manifest for diagnosis; do not acquire or promote. If payload identity matches, create a temporary visible payload-only view under ~/adamArchives/Adam/workspace-control-tmp/ using hardlinks to exactly those 14 non-.cache regular files (preserving relative paths, no symlinks, no source mutation), verify the view has exact count/bytes/hashes, then use the installed root-owned trusted cache manager from runtime 42cf6a0bebbc79f4d5657486c7b259bfcc4a5b7a to acquire that payload-only view into quarantine and promote atomically. Require promotion receipt PASS, candidate_promotion_authorized=false, quarantine_destroyed=true, offline_complete=true, exact immutable Qwen revision/license/safetensors risk metadata, then verify the promoted object as ci-research-engine with read_only=true and rehash both promoted weight shards. Do not run inference, enable model-eval, download alternate weights, mutate the original prefetched source, or mutate production/scientific state.

## Remaining work

- Classify the existing Qwen local_dir tree using the exact owning prefetch artifact_files semantics; if the non-.cache payload is exactly the durable 14-file/9342907469-byte identity, create a temporary payload-only view that excludes transport metadata and promote/verify that exact payload without inference.
- Promote/build and pin the exact qwen35-vllm-cu129-image-native-sampler-v3 runtime/dependency object independently of model weights, suitable for read-only offline model-eval.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- Before real Qwen acquisition, reconcile the raw local_dir tree with the owning prefetch payload semantics. The original prefetch helper excludes any file beneath a `.cache` path; the failed preflight counted all files. Promotion may proceed only if the non-.cache regular-file payload is exactly 14 files / 9342907469 bytes and both primary weight hashes match.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
