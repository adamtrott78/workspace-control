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
- Remote checkpoint: f95696ecc00110754b2479d4efe5e265379ed5a3
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

DIAGNOSIS IS COMPLETE; do not create another registry epoch bump. Apply the validated reconciliation-controller race hotfix only. From a clean detached workspace-control worktree at exact SHA f95696ecc00110754b2479d4efe5e265379ed5a3, run `WORKSPACE_CI_RECONCILE_HOTFIX_EXPECTED_SHA=f95696ecc00110754b2479d4efe5e265379ed5a3 sudo -E bash <worktree>/scripts/hotfix_lambda_ci_reconcile_controller_race.sh`. The helper must report HOTFIX_SOURCE_BLOB_PREFLIGHT=PASS, then prove a terminal root receipt with policy_equivalent_to_observed_main=true, active_projects=[research-engine], planned_projects_skipped=[padataset], mutation_performed=true, and finally RUN3_RECONCILIATION_PLANE=PASS. If it fails, do not widen policy or bump the registry; inspect the complete helper output plus `systemctl status workspace-ci-reconcile-controller.service` and `journalctl -u workspace-ci-reconcile-controller.service -n 200 --no-pager`. After PASS, checkpoint the reconciliation plane before starting research-engine CPU/gpu-small/model-eval regressions.

## Remaining work

- Run 3 immediate: apply validated poller-only PR #239 hotfix from exact f95696ecc00110754b2479d4efe5e265379ed5a3 and require RUN3_RECONCILIATION_PLANE=PASS.
- Run 3: checkpoint the accepted Git-driven reconciliation controller/root path; only then mark git_driven_project_reconciliation VALIDATED.
- Run 3: run research-engine CPU, gpu-small and at least one already-accepted model-eval regression through the generic installed path, with clean terminal receipts and zero residue/quarantine.
- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard PADataset by registry/manifest reconciliation only, then execute non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal research-engine/PADataset filesystem/process/cache isolation and verify zero controller/provisioner/runtime source changes during PADataset onboarding.
- Final: prove a third approved repository requires only registry + manifest + thin launcher binding and freeze the reusable operating contract.

## Blockers / gates

- Live reconciliation controller still runs the pre-hotfix exact-current-main poller. Apply the validated PR #239 poller-only hotfix and require a terminal root reconciliation PASS before triggering any research-engine regression.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
