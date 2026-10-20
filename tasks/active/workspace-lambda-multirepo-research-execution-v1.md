<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-lambda-multirepo-research-execution-v1
- Title: Workspace Lambda Multi-Repository Research Execution v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Generalize the accepted GitHub-to-Lambda execution substrate from a research-engine-specific pilot into a reusable, fail-closed, manifest-driven research compute control plane that can execute bounded candidate code from research-engine, PADataset, and future explicitly authorized research repositories without per-task controller/provisioner/runtime patches or routine human SSH/sudo intervention.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 8a01cd0fc7e373c5745782916eadc2de57d9f3f8
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: a4a5e1a2afc004b484542d5a71746e6472154fdb
- Remote verified: true

## Next safe action

Merge this migration-PASS checkpoint. The registry epoch-only bump intentionally triggers `.github/workflows/lambda-ci-project-reconcile.yml` on the resulting workspace-control/main head without changing execution authority. Require that trusted workflow to PASS. Then, from a clean checkout at that exact resulting main SHA, stage the dedicated workspace-control read/actions token by running the installed `/opt/workspace-ci/reconcile-controller/stage-pat` as `ci-reconciler`, and execute `scripts/activate_lambda_ci_reconcile_controller.sh` via sudo with WORKSPACE_CI_MULTIREPO_EXPECTED_SHA bound to that main SHA. Return the complete activation/root-reconciliation receipt before triggering research-engine regressions. PADataset remains untouched.

## Remaining work

- Run 3: activate and prove the dedicated Git-driven reconciliation controller/root path against the trusted current-main reconciliation workflow; then mark git_driven_project_reconciliation VALIDATED.
- Run 3: run research-engine CPU, gpu-small and at least one already-accepted model-eval regression through the generic installed path, with clean terminal receipts and zero residue/quarantine.
- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard PADataset by registry/manifest reconciliation only, then execute non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal research-engine/PADataset filesystem/process/cache isolation and verify zero controller/provisioner/runtime source changes during PADataset onboarding.
- Final: prove a third approved repository requires only registry + manifest + thin launcher binding and freeze the reusable operating contract.

## Blockers / gates

- One-time reconciliation credential/activation gate: stage a dedicated workspace-control read/actions token as ci-reconciler and activate workspace-ci-reconcile-controller.service after the trusted reconciliation workflow passes on the current main head.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
