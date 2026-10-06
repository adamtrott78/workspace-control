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

Human-only credential gate: on Lambda use a clean detached workspace-control tree exactly at `fbd9a1b9a0f0d811641fd4091c9aed3528b5ab16` and run `scripts/launch_lambda_ci_p3_cpu.py` under sudo with `WORKSPACE_CI_P3_AUTHORIZED=YES`. Do not rebuild PostgreSQL/pgvector; the isolated runtime already passed and remains installed. Paste a newly-created short-lived research-engine Administration:write PAT only into the hidden prompt. The launcher will now stream runner output live while retaining the durable log. Fresh run 37408781519 is already queued on cpu-test-v2.

## Remaining work

- Ensure the exposed PAT is revoked/deleted; create a new short-lived research-engine Administration:write token only for the next one-job JIT launch.
- Launch fresh run 37408781519 with the live-output P3 launcher; do not rebuild the isolated PostgreSQL runtime.
- Watch live stage output in the terminal and immediately consume the GitHub run/artifacts when terminal.
- Continue bounded repair/re-run until install/compile/pytest PASS.
- Only after P3 full PASS begin P4 GPU validation.

## Blockers / gates

- Human-only JIT credential gate: launch fresh P3 run 37408781519 using the live-output launcher from exact workspace-control fbd9a1b9a0f0d811641fd4091c9aed3528b5ab16 or a later exact reviewed main containing the same launcher, with a newly-created short-lived research-engine Administration:write token.
- The PAT previously pasted into chat is compromised and must remain revoked; never reuse it.
- Heartbeat v4 plugin updates currently return Session terminated; this does not block execution because authoritative Git/task/GitHub state is durable.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
