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

## Current stage

project_isolation_and_cache_validation

## Next safe action

Begin P5 static/recovery analysis from the accepted workspace-control architecture and current main: re-read `architecture/lambda-self-hosted-execution-v1.md`, `architecture/lambda-ci-controller-adapter.v1.md`, `architecture/lambda-ci-provisioner-protocol.v1.md`, `architecture/lambda-ci-systemd-profiles.v1.json`, and the current controller/provisioner scripts/tests. Compare those accepted contracts against the proven P2-P4 manual JIT launchers and identify the minimal implementation delta for an autonomous unprivileged `ci-controller` + narrow root provisioner. Do not mutate the live Lambda host until the P5 static implementation is CI-green.

## Remaining work

- P5: re-read the accepted scale-set/controller/provisioner architecture and current implementation artifacts, then identify the smallest delta from the proven P2-P4 manual JIT launchers to an autonomous controller.
- P5: implement hosted-CI validation for an unprivileged ci-controller listener using the pinned official actions/scaleset client (or accepted adapter) and a narrow local root provisioner with no GitHub credential.
- P5: on Lambda, install/enable only the accepted controller/provisioner pieces and prove ChatGPT can trigger a deliberate bounded failure, consume evidence, repair, and rerun PASS without human SSH or PAT relay.
- P5: prove controller restart/recovery, one-job cleanup, credential non-exposure, and kill-switch behavior.
- P6: perform second-project isolation pilot under a distinct UID/root/cache and prove mutual denial.

## Blockers / gates

- P5 controller/provisioner acceptance is not yet implemented on the live Lambda host; routine JIT execution still requires the operator's local sudo/PAT relay.
- P5 must not persist a broad GitHub credential in root context or grant arbitrary command/device/path selection to the network-facing controller.
