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

Human-only gate: on Lambda use one clean detached workspace-control tree exactly at `a1c12e878ac26c7ddedd84b1eb25acc0c52fed7c`. First run `scripts/bootstrap_lambda_ci_p3_postgres_runtime.sh` under sudo with `WORKSPACE_CI_P3_RUNTIME_AUTHORIZED=YES` and `WORKSPACE_CI_P3_RUNTIME_EXPECTED_SHA=a1c12e878ac26c7ddedd84b1eb25acc0c52fed7c`. If and only if it reports P3_ISOLATED_RUNTIME_BOOTSTRAP=PASS, run `scripts/launch_lambda_ci_p3_cpu.py` under sudo with `WORKSPACE_CI_P3_AUTHORIZED=YES` and paste a short-lived research-engine Administration:write token only into the hidden prompt. Corrected run 37398604653 is already queued on cpu-test-v2.

## Remaining work

- On Lambda, execute the isolated runtime bootstrap from exact workspace-control a1c12e878ac26c7ddedd84b1eb25acc0c52fed7c and require P3_ISOLATED_RUNTIME_BOOTSTRAP=PASS.
- Only after runtime PASS, launch the cpu-test-v2 one-job JIT runner from the same exact tree and service queued run 37398604653.
- Immediately consume run 37398604653 and its receipt when terminal; continue bounded repair/re-run without waiting if any new issue is demonstrated.
- Only after P3 full PASS begin P4 GPU validation.

## Blockers / gates

- Human-only root/credential gate: build and smoke-test the isolated PostgreSQL 14.24 + pgvector 0.8.6 runtime on Lambda, then provide a short-lived research-engine Administration:write token only to the hidden JIT launcher prompt.
- P3 run 37398604653 must reach full candidate install/compile/pytest PASS before P4.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
