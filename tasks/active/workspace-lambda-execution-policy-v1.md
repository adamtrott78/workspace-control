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

On Lambda, perform a narrow read-only root receipt/residue verification for trusted-cache canary CPU request 065b4d15-917f-5e67-92ee-6e2591f70138 after successful GitHub run 37560256841. Require the root runtime receipt to bind the same request/candidate/workload identity and report RUNNER_EXITED_CLEANLY with runner_exit_code=0, project UID cleanup=true, runner/staging workspace destroyed=true, GitHub credential absent, and JIT config not persisted. Independently require the exact job/staging directories to be absent and no ci-research-engine processes to remain. Do not mutate the promoted canary or production/scientific state. Only after this cleanup proof passes may the exact Qwen3.5-4B pinned model/runtime object be acquired/promoted through the trusted cache manager; model-scale workload routes remain non-live until their later gate.

## Remaining work

- Verify the root runtime receipt and residue-free cleanup for canary CPU request 065b4d15-917f-5e67-92ee-6e2591f70138.
- Promote/verify the exact Qwen3.5-4B model/runtime object from existing pinned research-engine evidence without enabling model evaluation yet.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- Root runtime receipt and residue-free cleanup for trusted-cache canary CPU request 065b4d15-917f-5e67-92ee-6e2591f70138 must pass before any real model/runtime object is promoted.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
