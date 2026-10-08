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
- Remote checkpoint: 3eb87841018bf2d86ec4af04b610e086f0abc8da
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: fa0ff6f1a4a46fd0295e45df401aa8361d220c86
- Remote verified: true

## Next safe action

Install workspace-control exact SHA 3eb87841018bf2d86ec4af04b610e086f0abc8da on Lambda with the accepted exact-SHA bootstrap. Verify runtime blob 24d4457d55503bbdbbd5a768b4889070e348ed4a, provisioner-service blob 74e7838e44eebd3a73dde620a61d3b052d78e466, trusted-cache manager blob a97cb0be0e8f1f53504b33aed7c31a5aa6cb7807, project manifest blob 2f019505d4ea7257d1067fb25b8d1d23f2e48ee1, and policy blob 5349572dd7982858c4526bafc16e53d7266cf8c8. Then run a root-only synthetic cleanup-quarantine canary against a temporary StateStore and fake launcher using the installed modules; do not submit a GitHub job or quarantine a live lane. Require RuntimeCleanupError to persist quarantine, block a second admission after service reconstruction, leave production lane state untouched, and clean the temporary canary directory.

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
