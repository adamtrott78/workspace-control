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

CREDENTIAL CAPABILITY GATE PASS. From a clean detached workspace-control worktree at exact validated hotfix SHA f95696ecc00110754b2479d4efe5e265379ed5a3, run the validated `scripts/hotfix_lambda_ci_reconcile_controller_race.sh` helper with WORKSPACE_CI_RECONCILE_HOTFIX_EXPECTED_SHA set to that SHA. This is now the bounded reconciliation-plane acceptance: it may reinstall the identical validated poller blob and restart only workspace-ci-reconcile-controller.service, then must prove policy_equivalent_to_observed_main=true, active_projects=[research-engine], planned_projects_skipped=[padataset], mutation_performed=true, PADataset host state still absent, and print RUN3_RECONCILIATION_PLANE=PASS. Do not change policy, bump registry_epoch, rerun the full migration, or onboard PADataset.

## Remaining work

- Run 3 immediate: restart only workspace-ci-reconcile-controller.service through the validated PR #239 acceptance path and require RUN3_RECONCILIATION_PLANE=PASS with policy equivalence, active research-engine only, PADataset skipped, and mutation_performed=true.
- Run 3: checkpoint the accepted Git-driven reconciliation controller/root path; only then mark git_driven_project_reconciliation VALIDATED.
- Run 3: run research-engine CPU, gpu-small and at least one already-accepted model-eval regression through the generic installed path, with clean terminal receipts and zero residue/quarantine.
- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard PADataset by registry/manifest reconciliation only, then execute non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal research-engine/PADataset filesystem/process/cache isolation and verify zero controller/provisioner/runtime source changes during PADataset onboarding.
- Final: prove a third approved repository requires only registry + manifest + thin launcher binding and freeze the reusable operating contract.

## Blockers / gates

- Credential capability gate is PASS. The reconciliation controller remains intentionally stopped pending one bounded restart/acceptance operation that must produce a terminal PASS receipt with policy_equivalent_to_observed_main=true, active_projects=[research-engine], planned_projects_skipped=[padataset], and mutation_performed=true.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
