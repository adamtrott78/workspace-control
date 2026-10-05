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

threat_model_and_architecture_research

## Next safe action

Research current GitHub self-hosted runner behavior and security from primary sources, then produce a threat model and architecture decision for a project-isolated Lambda execution lane. Do not install/register any runner or change existing CI yet. Preserve existing GitHub-hosted CI as the known-good control and design the research-engine pilot so it can prove closed-loop ChatGPT -> GitHub -> Lambda -> GitHub execution without production-state access.

## Remaining work

- Research current GitHub self-hosted runner security, ephemeral/JIT configuration, repository scoping, token/secret behavior, artifacts/logs, and billing.
- Compare isolation architectures: dedicated Unix user, disposable VM, rootless container, systemd sandbox, and hybrid runner+job sandbox.
- Define project-specific filesystem, credentials, network, production-state, GPU, cache, concurrency, and cleanup boundaries.
- Select the smallest safe research-engine pilot architecture.
- Only after design acceptance, create the Lambda runner foundation and a no-op isolation test before real CI/GPU workloads.

## Blockers / gates

- None recorded.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
