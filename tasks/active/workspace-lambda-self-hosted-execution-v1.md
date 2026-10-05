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

Execute the tracked read-only P0 host probe from `workspace-control:lambda-self-hosted-execution-v1-design@0f3ff4531f70ed4f65392030a8e308cab7ea19b5` on Lambda and return `lambda-runner-host-probe.json`. This probe writes only its diagnostic output under the visible workspace-control-tmp root and must not use sudo or mutate users/services/firewall/runner registration. After analyzing that receipt, implement the bootstrap/controller/systemd/kill-switch artifacts against the actual host capabilities before any runner registration.

## Remaining work

- Run the tracked P0 read-only Lambda host probe and analyze the JSON receipt.
- Using only the observed host facts, implement/review root-owned controller, dedicated-user bootstrap, systemd sandbox profile, kill switch, and trusted research-engine trigger workflow without registering the runner yet.
- Perform P2 isolation acceptance: create ci-research-engine, prove denial of /home/atrott, unrelated projects, sudo, Docker socket, production DB/daemon/broker, then execute one no-op ephemeral repo-scoped runner job.
- Perform P3 CPU validation with ephemeral project environment/database and GitHub artifact return.
- Perform P4 bounded GPU validation with process/VRAM cleanup receipt.
- Perform P5 closed-loop acceptance where ChatGPT creates a deliberate failure, triggers Lambda, diagnoses/fixes it, reruns to PASS, and consumes a returned artifact without human SSH.
- Only after research-engine acceptance, opt in a second project such as PADataset under a separate UID/root/cache and prove cross-project denial.

## Blockers / gates

- P0 host facts must be collected from the actual Lambda before choosing/enforcing systemd device/network/filesystem restrictions. No runner/user/service/firewall mutation is authorized before this receipt is analyzed.
- workspace-control evidence-first workflow PR #70 remains blocked by GitHub-hosted runner allocation: two attempts were cancelled after 15 minutes with runner_id=0 and zero executed steps. This is external scheduling evidence, not a test failure.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
