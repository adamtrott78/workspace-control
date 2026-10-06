<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-lambda-self-hosted-execution-v1
- Title: Workspace Lambda Self-Hosted Execution v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Design, validate, and if safety gates pass pilot a project-isolated GitHub Actions execution lane on the existing Lambda workstation so ChatGPT/GitHub-driven software work can execute and validate directly in the real target environment without routine human-terminal mediation, while preserving project authority, minimizing host risk, and keeping existing GitHub-hosted CI as the known-good control.

## Parent execution owner

research-engine-local-extract-redesign-v1

## Current stage

research_engine_pilot

## Next safe action

On Lambda, create a clean detached workspace-control worktree exactly at `c2e2c1a6a1f75cca424e94041e39c1e375ce63ca`, then run `scripts/launch_lambda_ci_p3_cpu.py` under sudo with `WORKSPACE_CI_P3_AUTHORIZED=YES`. Paste a short-lived fine-grained GitHub PAT scoped only to `adamtrott78/research-engine` with repository Administration:write into the hidden prompt. Do not put the token in chat, Git, argv, environment, or a file. The trusted P3 run is already queued as 37394877505. After launcher exit, return only the non-secret `lambda-ci-p3-launcher.json` receipt; ChatGPT will inspect the GitHub run/artifact directly.

## Remaining work

- Execute the reviewed P3 one-job JIT launcher on Lambda using a short-lived research-engine Administration:write token pasted only into the hidden local prompt.
- Inspect GitHub run 37394877505 and lambda-ci-p3-receipt; if failure occurs, diagnose exact host/candidate incompatibility and iterate through a new exact SHA/run.
- If P3 passes, checkpoint CPU validation and begin P4 bounded GPU validation with explicit device grant and post-job GPU/process cleanup.
- P5: install/accept autonomous scale-set listener + narrow root provisioner and prove closed-loop fail-diagnose-fix-rerun-PASS with no human SSH/token relay.
- P6: second-project isolation pilot under separate UID/root/cache.

## Blockers / gates

- P3 run 37394877505 requires one local short-lived research-engine Administration:write token to mint the one-job JIT runner because the autonomous scale-set controller is intentionally deferred until P5.
- P3 may reveal host-specific PostgreSQL/pgvector or candidate-test failures; those should be diagnosed from the returned GitHub receipt/logs rather than bypassing isolation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
