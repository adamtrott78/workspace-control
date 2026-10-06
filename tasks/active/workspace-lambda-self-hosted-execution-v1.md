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

Human-only credential gate: first revoke the fine-grained PAT that was pasted into chat. Then, on Lambda, create/reuse a clean detached workspace-control tree exactly at `744e7f67e22fb5bd7de35ad8a0284a63f2b2cced` and run only `scripts/launch_lambda_ci_p3_cpu.py` under sudo with `WORKSPACE_CI_P3_AUTHORIZED=YES`. Do not rerun the PostgreSQL runtime bootstrap; the isolated PostgreSQL 14.24 + pgvector 0.8.6 runtime already passed and is installed read-only. Paste a newly-created short-lived research-engine Administration:write token only into the hidden prompt. Fresh run 37407910754 is already queued on cpu-test-v2.

## Remaining work

- Revoke/delete the fine-grained PAT that was pasted into chat; never reuse it.
- On Lambda, execute scripts/launch_lambda_ci_p3_cpu.py from exact workspace-control 744e7f67e22fb5bd7de35ad8a0284a63f2b2cced. Do not rebuild PostgreSQL/pgvector; the isolated runtime already passed and remains installed.
- Paste a newly-created short-lived research-engine Administration:write token only into the hidden local prompt to service queued run 37407910754.
- Immediately consume run 37407910754 and its receipt when terminal; continue bounded repair/re-run without waiting if any new issue is demonstrated.
- Only after P3 full PASS begin P4 GPU validation.

## Blockers / gates

- Human-only JIT credential gate: run the fixed P3 launcher from exact workspace-control 744e7f67e22fb5bd7de35ad8a0284a63f2b2cced and paste a newly-created short-lived research-engine Administration:write token only into the hidden prompt. The previously pasted token is compromised and must be revoked.
- Fresh P3 run 37407910754 must reach full candidate install/compile/pytest PASS before P4.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
