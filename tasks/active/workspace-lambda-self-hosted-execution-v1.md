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

Begin P3 static implementation: inspect the accepted research-engine CI commands and project dependencies, then add a trusted default-branch Lambda CPU-validation workflow plus a P3 JIT launcher/profile that checks out exact PR #95 head `ab36b358a0c7ac33d2887fa681f418033554eae0`, uses `persist-credentials:false`, creates an ephemeral ci-research-engine-owned PostgreSQL test cluster on a Unix socket, executes the real compile/unit/integration validation on Lambda, uploads a structured receipt, and destroys its workspace/database afterward. Do not access production PostgreSQL, production daemon state, or GPUs in P3.

## Remaining work

- P3: add a trusted default-branch CPU-validation workflow that checks out an exact same-repository PR head with persist-credentials=false, creates a fresh venv, launches an ephemeral ci-research-engine-owned PostgreSQL cluster over a Unix socket, installs/tests the candidate, and uploads a structured receipt.
- P3: launch one ephemeral CPU runner, execute candidate research-engine PR #95 exact head ab36b358a0c7ac33d2887fa681f418033554eae0, inspect logs/artifacts, and prove cleanup.
- P4: add bounded GPU validation with explicit device grant and post-job GPU/process cleanup.
- P5: install/accept the autonomous scale-set listener + root provisioner path and prove ChatGPT fail-diagnose-fix-rerun-PASS acceptance without human SSH/token relay.
- P6: second-project cross-project isolation pilot under separate UID/root/cache.

## Blockers / gates

- P3 must use an ephemeral test database owned by ci-research-engine over a Unix socket or equally isolated endpoint; production PostgreSQL remains forbidden.
- Until the autonomous scale-set controller/GitHub App path is installed, each new JIT runner still requires a local short-lived repository Administration token bootstrap; this is acceptable for P3/P4 but must be eliminated before P5 closed-loop acceptance.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
