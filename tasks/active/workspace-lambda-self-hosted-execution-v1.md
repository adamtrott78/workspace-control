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

Run the tracked read-only P1 compatibility probe from workspace-control PR #72 head `46d3d33aa560df2adf90137e0951097ed973ee1d` on Lambda and return `lambda-runner-p1-probe.json`. The probe writes only its receipt under the visible workspace-control-tmp directory and performs no user/service/runner/firewall/cgroup mutation. In parallel, allow PR #72 repository validation to instantiate. P2 remains explicitly unauthorized until the compatibility receipt, static tests, and later non-runner transient sandbox probes pass.

## Remaining work

- Run scripts/lambda_runner_p1_compatibility_probe.py read-only on Lambda and analyze the JSON receipt.
- Use that receipt to finalize disk/quota, PostgreSQL ephemeral-test-DB, firewall/network and controller build strategy.
- Run repository validation for PR #72 and fix only demonstrated static/test defects.
- Perform non-runner transient sandbox probes for ProtectProc/ProcSubset, IPAddressDeny/Allow, and DevicePolicy=closed CUDA access.
- Only if all P1 gates pass, authorize P2 one-time host bootstrap and first no-op ephemeral repository-scoped runner.

## Blockers / gates

- P1 compatibility receipt from the actual Lambda is still required before P2: resolve /srv filesystem/quota support, PostgreSQL bindir, firewall/nft state, and remaining sandbox compatibility facts.
- workspace-control PR #72 repository validation has not yet instantiated a workflow run; P2 remains unauthorized until static tests validate.
- Transient systemd device/network probes remain required after the read-only compatibility receipt and before any real runner registration.
- workspace-control evidence-first workflow PR #70 remains separately blocked by GitHub-hosted runner allocation and does not block this P1 branch.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-self-hosted-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
