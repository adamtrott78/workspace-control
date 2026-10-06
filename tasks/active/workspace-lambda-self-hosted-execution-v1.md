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

Human live prerequisite only: on Lambda use a clean detached workspace-control tree exactly at `2b026c41f6dd8e3fcaa5e30fddaedb9babe09391` and run `scripts/bootstrap_lambda_ci_go_toolchain.sh` via sudo with `WORKSPACE_CI_GO_BOOTSTRAP_AUTHORIZED=YES` and `WORKSPACE_CI_GO_EXPECTED_SHA=2b026c41f6dd8e3fcaa5e30fddaedb9babe09391`. It must download go1.26.3 as ci-controller, verify SHA256 `2b2cfc7148493da5e73981bffbf3353af381d5f93e789c82c79aff64962eb556`, promote only `/opt/workspace-ci/go/1.26.3` as root-owned non-group/world-writable runtime, leave system Go/apt untouched, and emit a visible receipt. Do not retry the P5 service install until that receipt is reviewed.

## Remaining work

- P5 live prerequisite: install the exact pinned Go 1.26.3 runtime under /opt/workspace-ci/go/1.26.3 using scripts/bootstrap_lambda_ci_go_toolchain.sh from workspace-control 2b026c41f6dd8e3fcaa5e30fddaedb9babe09391 and review its receipt.
- P5 live gate A retry: rerun scripts/bootstrap_lambda_ci_p5.sh from the same exact SHA with controller activation disabled; require provisioner/socket PASS.
- P5 live gate B: stage the clean research-engine PAT directly as ci-controller using /opt/workspace-ci/controller/stage-pat; never paste token into chat.
- P5 live gate C: activate controller and require controller/provisioner both active.
- P5 autonomous acceptance: trigger trusted CPU scale-set demand and prove autonomous provision/cleanup/evidence without human SSH/PAT relay.
- P5 recovery: prove restart/recovery, replay protection, cleanup-failure blocking, and kill switch.
- P6: second-project isolation pilot under distinct UID/root/cache.

## Blockers / gates

- P5 isolated Go 1.26.3 runtime is not yet installed on Lambda; the accepted toolchain bootstrap must pass before retrying service install.
- Controller activation remains intentionally gated on later ci-controller-owned credential staging.
