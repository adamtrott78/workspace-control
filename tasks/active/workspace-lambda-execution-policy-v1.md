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
- Remote checkpoint: b6bf6ca2618cc747bba974f71f52901907cea4c5
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 9b025b3b1092d1c4e0c1f98678472341d26ee354
- Remote verified: true

## Next safe action

Install and activate exact workspace-control 4d4d14480f2cd6b573e33b10efc61a81a316327a on Lambda from a fresh detached clean worktree using the accepted P5 bootstrap with WORKSPACE_CI_P5_INSTALL_AUTHORIZED=YES, WORKSPACE_CI_P5_EXPECTED_SHA=4d4d14480f2cd6b573e33b10efc61a81a316327a, and WORKSPACE_CI_P5_ACTIVATE_CONTROLLER=YES. Do not restage the controller token. After activation, capture CPU/GPU controller NRestarts and active/running state, wait 8 seconds, capture again, and require both services remain active/running with zero restart delta and no recent 403/controller-exited errors. Only then trigger a NEW /lambda-ci-p5 f5ba8278d7dfa22e63623ddf51896a6dec002813 on PR #106; use the GitHub-hosted /lambda-ci-cancel <run_id> control for stale acceptance cancellation. Do not enable model-scale classes or gpu-heavy.

## Remaining work

- Install and activate exact terminal-safe workspace-control 4d4d14480f2cd6b573e33b10efc61a81a316327a, prove restart-delta stability with the now-complete read-only controller credential, then run fresh CPU and gpu-small admission-v2 acceptance and validate root receipts plus residue-free cleanup.
- Implement trusted acquisition/quarantine/promotion and read-only content-addressed model/runtime cache semantics.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- Exact terminal-safe workspace-control 4d4d14480f2cd6b573e33b10efc61a81a316327a is validated but not yet installed on Lambda. Install/activate it before any new acceptance run.
- After activation, prove CPU/GPU controllers are active/running with no NRestarts delta over a bounded 8-second window before launching a fresh CPU acceptance.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
