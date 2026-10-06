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

Human live gate A retry only: on Lambda use a clean detached workspace-control tree exactly at `2b026c41f6dd8e3fcaa5e30fddaedb9babe09391` and run `scripts/bootstrap_lambda_ci_p5.sh` via sudo with `WORKSPACE_CI_P5_INSTALL_AUTHORIZED=YES`, `WORKSPACE_CI_P5_EXPECTED_SHA=2b026c41f6dd8e3fcaa5e30fddaedb9babe09391`, and no `WORKSPACE_CI_P5_ACTIVATE_CONTROLLER` flag. The isolated Go prerequisite is already PASS at `/opt/workspace-ci/go/1.26.3`; do not rerun the Go bootstrap unless the prefix is missing or version-drift evidence appears. This service bootstrap must install/start only the root provisioner, verify `/run/workspace-ci/provisioner.sock` is `root:workspace-ci-controller` mode `0660`, leave `workspace-ci-controller` installed but inactive, handle no GitHub credential, and emit a visible receipt. Do not stage the PAT or activate the controller until that provisioner-only receipt is reviewed.

## Remaining work

- P5 live gate A retry: run scripts/bootstrap_lambda_ci_p5.sh from exact workspace-control 2b026c41f6dd8e3fcaa5e30fddaedb9babe09391 with controller activation disabled; require provisioner service/socket PASS and review receipt.
- P5 live gate B: stage the existing clean research-engine PAT directly as ci-controller using /opt/workspace-ci/controller/stage-pat; never paste token into chat.
- P5 live gate C: rerun the exact P5 bootstrap with WORKSPACE_CI_P5_ACTIVATE_CONTROLLER=YES and require controller/provisioner both active.
- P5 autonomous acceptance: trigger trusted CPU scale-set demand and prove autonomous provision/cleanup/evidence without human SSH/PAT relay.
- P5 recovery: prove controller restart/recovery, replay protection, cleanup-failure blocking, and kill switch.
- P6: perform second-project isolation pilot under distinct UID/root/cache and prove mutual denial.

## Blockers / gates

- P5 live gate A service install has not yet been retried after the isolated Go prerequisite PASS; provisioner/controller code is not yet accepted on-host.
- Controller activation remains intentionally gated on later ci-controller-owned credential staging; do not stage or activate the controller before provisioner-only receipt review.
