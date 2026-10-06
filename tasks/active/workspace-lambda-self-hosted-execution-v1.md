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

Implement the P5 installation/bootstrap layer on a fresh workspace-control branch from `c23ce9a7031d567981a56a49261fdf0508b68ed8`: root-owned `workspace-ci-provisioner.service`, unprivileged `workspace-ci-controller.service`, `/run/workspace-ci/provisioner.sock` root:workspace-ci-controller 0660, controller-only credential-file ownership, pinned controller binary build/install, and kill-switch integration. Add executable regressions for unit users/groups, credential separation, socket permissions, no-network provisioner policy, controller network access, restart policy, and uninstall/rollback. Do not mutate Lambda until the install/bootstrap PR is CI-green.

## Remaining work

- P5: implement root-owned install/bootstrap for workspace-ci-provisioner and unprivileged ci-controller systemd units, controller-only credential file, socket ownership/mode, and kill-switch integration.
- P5: validate install/bootstrap statically and with executable unit/property regressions; merge before host mutation.
- P5: install/enable the accepted units on Lambda and run a no-op/autonomous CPU pilot proving GitHub demand creates and cleans one runner without human SSH/PAT relay.
- P5: prove controller restart/recovery, provisioner replay protection, cleanup failure blocking, and kill-switch behavior.
- P6: perform second-project isolation pilot under a distinct UID/root/cache and prove mutual denial.

## Blockers / gates

- P5 service installation/bootstrap is not yet implemented or accepted; live Lambda still requires manual launchers until root-owned units and credential-file boundaries are installed and proven.
- P5 live activation must not place GitHub credentials in root/provisioner context and must preserve P2-P4 runner isolation.
