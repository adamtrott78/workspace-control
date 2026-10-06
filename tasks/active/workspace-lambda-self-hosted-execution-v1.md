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

Human live gate A only: on Lambda, use a clean detached workspace-control tree exactly at `7febbb619962bd32e8a6e68c70e38b869affc6e7` and run `scripts/bootstrap_lambda_ci_p5.sh` via sudo with `WORKSPACE_CI_P5_INSTALL_AUTHORIZED=YES`, `WORKSPACE_CI_P5_EXPECTED_SHA=7febbb619962bd32e8a6e68c70e38b869affc6e7`, and no controller-activation flag. The bootstrap must fail closed before mutation if Go <1.26.3 or host prerequisites drift. On PASS it installs/starts only the root provisioner, verifies `/run/workspace-ci/provisioner.sock` root:workspace-ci-controller 0660, leaves the controller installed but inactive, handles no GitHub credential, and emits a receipt under the visible workspace-control-tmp directory. Do not stage or activate the controller until that receipt is reviewed.

## Remaining work

- P5 live gate A: run the exact-SHA install bootstrap on Lambda with controller activation disabled; require provisioner service/socket PASS and no production-service changes.
- P5 live gate B: stage the existing clean research-engine PAT directly as ci-controller using /opt/workspace-ci/controller/stage-pat; do not paste the token into chat.
- P5 live gate C: rerun exact-SHA bootstrap with WORKSPACE_CI_P5_ACTIVATE_CONTROLLER=YES and require controller/provisioner both active.
- P5 acceptance: trigger a trusted scale-set CPU job from GitHub and prove autonomous runner provisioning, exact candidate validation, cleanup, evidence consumption, repair/rerun without human SSH/PAT relay.
- P5 recovery: prove controller restart/recovery, replay protection, cleanup-failure blocking, and kill switch.
- P6: perform second-project isolation pilot under a distinct UID/root/cache and prove mutual denial.

## Blockers / gates

- P5 live services are not yet installed on Lambda; manual JIT launchers remain the active path until the accepted install bootstrap passes on-host.
- Controller activation remains intentionally gated on one-time ci-controller-owned credential staging.
