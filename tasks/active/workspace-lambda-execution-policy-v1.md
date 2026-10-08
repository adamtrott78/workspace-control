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

uv is absent on Lambda. Acquire uv as a separately pinned trusted package before benchmarking it: exact upstream release astral-sh/uv 0.12.23, immutable release tag 0.12.23 / target commit 46b84fd0bfec23b72f29e8e2185ba68a65052f48, x86_64-unknown-linux-gnu archive SHA-256 9167d72b3319674b6303c4cbe071854bba13ebdf3d76b1a7cbdc175471fb66d6, upstream license MIT OR Apache-2.0. Do not use curl|sh or install into a candidate-writable global path. First rerun only the reflink/COW capability probe on /var/tmp and inspect the protected trusted-cache filesystem via sudo so set -e cannot abort on permissions. Then download the exact uv release archive to a visible temporary directory, verify its pinned digest and version, and promote only the extracted uv tool payload through lambda-ci-trusted-cache-v1 as artifact_kind=package with reviewed license/provenance. After that, benchmark uv offline against the existing trusted 196-wheel runtime object with no network, no Python downloads, no index, only-binary, require-hashes, and link-mode clone if COW works, otherwise copy. Do not use symlink mode or change candidate/global PATH permanently.

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
