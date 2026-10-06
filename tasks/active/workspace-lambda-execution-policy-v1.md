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
- Remote checkpoint: 4d4d14480f2cd6b573e33b10efc61a81a316327a
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 9b025b3b1092d1c4e0c1f98678472341d26ee354
- Remote verified: true

## Next safe action

First stop workspace-ci-controller.service before changing any more token permissions; leave the canceled run 37540379924 terminal. In GitHub fine-grained token settings for the existing research-engine controller token, keep Actions: Read and add Contents: Read plus Pull requests: Read only; do not grant Actions: Write and do not broaden repository scope. Before restarting any controller, run a non-secret ci-controller probe requiring HTTP 200 for: GET /actions/runs/37540379924, GET /actions/runs/37540379924/jobs?per_page=100, GET /contents/.github/workflows/lambda-ci-p5-autonomous.yml?ref=12dd0f2f9510f682f0b62fe8fdc9a63494da8d6d, and GET /pulls/106. Only after all four return 200, install and activate exact workspace-control 4d4d14480f2cd6b573e33b10efc61a81a316327a from a fresh detached clean worktree using the accepted P5 bootstrap. Prove CPU/GPU controllers active/running and no NRestarts delta over an 8-second window. Then trigger a NEW /lambda-ci-p5 f5ba8278d7dfa22e63623ddf51896a6dec002813; use the GitHub-hosted /lambda-ci-cancel <run_id> control for any stale acceptance cancellation. Do not enable model-scale classes or gpu-heavy.

## Remaining work

- Stop the crash-looping CPU controller, add Contents: Read and Pull requests: Read to the existing narrow research-engine controller token, prove all four attestor REST endpoints return HTTP 200, install exact terminal-safe workspace-control 4d4d14480f2cd6b573e33b10efc61a81a316327a, then run fresh CPU and gpu-small acceptance.
- Implement trusted acquisition/quarantine/promotion and read-only content-addressed model/runtime cache semantics.
- Run adversarial recovery, replay, cleanup, resource-exhaustion, cache-integrity, and concurrency acceptance.
- Run the first offline Qwen3.5-4B pinned-model pilot on gpu-small.
- Decide separately whether gpu-heavy/dual-GPU should be accepted.

## Blockers / gates

- CPU controller is crash-looping on GitHub Contents API 403 under live f2468001; stop the CPU controller before widening the existing token's remaining read permissions so the old binary cannot process stale canceled recovery metadata.
- Fine-grained research-engine controller token must include exactly the currently required read surface: Actions: Read (already proven), Contents: Read, and Pull requests: Read, while preserving existing runner/scale-set permissions and without Actions: Write.
- After all four attestor endpoint probes return HTTP 200, exact workspace-control 4d4d14480f2cd6b573e33b10efc61a81a316327a must be installed/activated and controller restart delta proven stable before a new CPU acceptance.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
