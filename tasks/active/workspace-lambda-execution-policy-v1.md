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
- Remote checkpoint: 21d90bc676198b64b79bab3c439e2d576c65cf00
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: fa0ff6f1a4a46fd0295e45df401aa8361d220c86
- Remote verified: true

## Next safe action

Begin timeout/OOM/disk-pressure failure-receipt validation without changing accepted runtime/model authority. First, audit and harden timeout handling in the root runtime launcher so a subprocess timeout explicitly terminates the transient systemd unit/systemd-run wrapper, records a deterministic failure classification/receipt, still performs project-UID/GPU/runtime/workspace cleanup verification, and never automatically retries. Validate with CPU-only regression tests before any live timeout canary. Then run one bounded cpu-test timeout canary if the implementation is fully validated; do not use gpu-small for timeout testing.

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
