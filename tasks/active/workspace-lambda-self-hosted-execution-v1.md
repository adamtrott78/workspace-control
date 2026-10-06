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

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: d33ca95a8d63d7e9f9d7f85afc1fa02540faff16
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: aa1cdaafb4728c70be7bab0041df5f395f16141c
- Remote verified: true

## Next safe action

Continue from the accepted live P5 baseline at workspace-control d33ca95a8d63d7e9f9d7f85afc1fa02540faff16 and research-engine aa1cdaafb4728c70be7bab0041df5f395f16141c. The research-engine autonomous cpu-test scale-set lane is accepted for routine bounded validation. Next, execute the P5 recovery/adversarial acceptance gate: test controller restart/recovery, replay protection, cleanup-failure blocking, and kill-switch behavior using the existing trusted P5 workflow and without restaging the PAT, rerunning the Go bootstrap, broadening provisioner network/device authority, or granting production/scientific-state access.

## Remaining work

- P5 recovery/adversarial acceptance: prove controller restart/recovery, replay protection, cleanup-failure blocking, and kill switch behavior without weakening the accepted live boundary.
- P5 cache/resource hardening: exercise trusted-cache immutability/invalidation and bounded concurrency/resource-failure paths.
- P6 second-project isolation pilot: opt in a second repository under a distinct UID/root/cache policy and prove mutual denial.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
