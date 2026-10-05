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

P2 is authorized. Create and validate a P2 implementation branch from workspace-control main after `2bbdb81f97b5ce7743074a71bd0554f47b75b4a0`. The P2 bootstrap must run root-only transient firewall/process/network/device isolation probes first and fail closed before mutation; only on PASS may it create `ci-controller`/`ci-research-engine`, `/srv/workspace-ci/research-engine` roots, install checksum-pinned runner/controller assets, and prepare the first repository-scoped one-job no-op runner. Do not expose controller/personal credentials to job code and do not touch production research-engine services/state.

## Remaining work

- P2: validate root firewall state and transient systemd process/network/device sandbox behavior.
- P2: create dedicated ci-controller and ci-research-engine identities and /srv/workspace-ci roots only after transient gates pass.
- P2: install the exact pinned Actions runner package and controller toolchain with checksum verification.
- P2: register and execute one repository-scoped one-job no-op runner; prove home/Docker/production-service/system write denial and cleanup.
- P3: CPU candidate validation with ephemeral environment/database and GitHub artifact return.
- P4: bounded GPU validation with explicit device grant and post-job GPU/process cleanup.
- P5: closed-loop ChatGPT fail-diagnose-fix-rerun-PASS acceptance without SSH.
- P6: second-project cross-project isolation pilot under separate UID/root/cache.

## Blockers / gates

- P2 must begin with root-only transient sandbox/firewall/device/network probes and stop before user/runner creation if any mandatory isolation primitive fails.
- A repository-scoped GitHub credential path for the first ephemeral runner must be resolved without exposing personal/controller credentials to job code.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
