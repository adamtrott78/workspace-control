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

Install and activate exact workspace-control 42cf6a0bebbc79f4d5657486c7b259bfcc4a5b7a on Lambda from a fresh detached clean worktree using the accepted P5 bootstrap. Then, using only the installed root-owned /opt/workspace-ci/cache-manager/lambda_ci_trusted_cache.py, create a temporary harmless canary source containing exactly `workspace-ci-trusted-cache-canary-v1\n`, acquire it into the root-owned research-engine quarantine with a descriptor bound to recipe implementation_sha 42cf6a0bebbc79f4d5657486c7b259bfcc4a5b7a, promote it, and require object id 5bf1fba5838c38e5ae8e3f69b108d4b3ca9b9090aad435214f55fa30a626c14d plus offline verify PASS. Preserve cpu/gpu controllers active and do not enable any model-scale route. After canary promotion, trigger a fresh `/lambda-ci-p5` against research-engine PR #106 candidate f5ba8278d7dfa22e63623ddf51896a6dec002813 and require the new trusted-cache canary assertions plus ordinary CPU/root cleanup acceptance to PASS.

## Remaining work

- Install exact workspace-control 42cf6a0bebbc79f4d5657486c7b259bfcc4a5b7a, promote the fixed harmless cache canary through root quarantine, and run the adversarial cpu-test consumer gate.
- Promote/verify the exact Qwen3.5-4B model/runtime object from existing pinned research-engine evidence without enabling model evaluation yet.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- Exact trusted-cache implementation 42cf6a0bebbc79f4d5657486c7b259bfcc4a5b7a is validated but not yet installed on Lambda.
- The harmless content-addressed cache canary must be promoted by the root-only manager and consumed successfully by the repinned cpu-test workflow before any real model/runtime object is promoted.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
