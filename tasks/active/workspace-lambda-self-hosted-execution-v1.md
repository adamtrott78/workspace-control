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

safe_runner_foundation

## Next safe action

Execute P2-A on Lambda from workspace-control main exactly at `fd3589a997219b4bd7d1895cb2eb20d1e8b5edcf`: run `scripts/bootstrap_lambda_ci_research_engine.sh` as root with `WORKSPACE_CI_P2_AUTHORIZED=YES` and `WORKSPACE_CI_P2_EXPECTED_SHA=fd3589a997219b4bd7d1895cb2eb20d1e8b5edcf`. The script must stop before persistent mutation if any transient isolation probe fails. On PASS, return the visible `lambda-ci-p2-bootstrap.json` receipt; P2-B runner registration remains separate.

## Remaining work

- Execute P2-A bootstrap on Lambda at the exact workspace-control main SHA and inspect its visible JSON receipt.
- If P2-A passes, implement/trigger P2-B: one repository-scoped JIT no-op runner under ci-research-engine with trusted default-branch workflow and artifact receipt.
- P3: CPU candidate validation with ephemeral environment/database and GitHub artifact return.
- P4: bounded GPU validation with explicit device grant and post-job GPU/process cleanup.
- P5: closed-loop ChatGPT fail-diagnose-fix-rerun-PASS acceptance without SSH.
- P6: second-project cross-project isolation pilot under separate UID/root/cache.

## Blockers / gates

- P2-A must PASS on the real Lambda before P2-B JIT runner registration.
- P2-B still requires a short-lived repository-admin credential path solely to mint the encoded JIT config; the credential must not be exposed to job code or persisted.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
