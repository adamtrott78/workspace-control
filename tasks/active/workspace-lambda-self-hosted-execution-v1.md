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

Implement and statically review P1 artifacts on the isolated design branch at be9b425b10898a4b5bf4301e8075bb44b2e62a80: a pinned `actions/scaleset` listener strategy, unprivileged `ci-controller`, narrow local-only root provisioner protocol/manifest, systemd sandbox profiles, trusted-write/read-only cache layout, corrected read-only filesystem/PostgreSQL/firewall/device/network probes, and kill-switch/uninstall path. Do not create users/services, install/register any runner, expose secrets, change firewall rules, or change existing GitHub-hosted CI until these artifacts and follow-up probes pass review.

## Remaining work

- P1 static implementation: pin actions/scaleset client identity/update policy; define unprivileged ci-controller; define narrow root provisioner IPC/request schema and root-owned project/profile manifest.
- Add corrected read-only host follow-up probes for /srv filesystem/quota support, PostgreSQL bindir/test DB strategy, firewall/nftables state, and transient systemd device/network restrictions.
- Implement/review systemd CPU/GPU sandbox profiles, trusted cache layout/manager, diagnostic retention, kill switch, and full uninstall/recovery path in Git only; do not activate yet.
- After static review and read-only compatibility PASS, perform P2 one-time root bootstrap: create ci-controller/ci-research-engine identities and roots, then one no-op repository-scoped one-job runner isolation test.
- Perform P3 CPU validation with ephemeral project environment/database and GitHub artifact return.
- Perform P4 bounded GPU validation with explicit device grant and process/VRAM cleanup receipt.
- Perform P5 closed-loop acceptance where ChatGPT creates a deliberate failure, triggers Lambda, diagnoses/fixes it, reruns to PASS, and consumes an artifact without human SSH.
- Only after research-engine acceptance, opt in PADataset under a separate scale set/UID/root/cache and prove cross-project denial.

## Blockers / gates

- No host mutation is authorized yet. P1 static artifacts must be implemented/reviewed first, and the remaining read-only host follow-ups must prove filesystem/quota, PostgreSQL test-database location, current firewall state, and systemd device/network policy compatibility.
- GitHub's actions/scaleset client is Public Preview; pin an exact version/commit and isolate it behind a narrow local adapter before relying on it.
- workspace-control evidence-first workflow PR #70 remains externally blocked by GitHub-hosted runner allocation after two 15-minute runner_id=0 / zero-step cancellations; this does not block design work here.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
