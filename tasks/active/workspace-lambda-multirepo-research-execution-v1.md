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
- Remote checkpoint: 8adfe21f553d4cf5c2d4ff3299d2ced611ec4fa1
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

VALIDATED LIVE REPAIR READY. Use exact workspace-control SHA 8adfe21f553d4cf5c2d4ff3299d2ced611ec4fa1 in a fresh detached worktree and execute `scripts/lambda_ci_reconciliation_socket_hotfix_v1.sh` with WORKSPACE_CI_RECONCILE_SOCKET_HOTFIX_EXPECTED_SHA set to that SHA. Before creating the fresh worktree, repair only the diagnosed stale index `.git/worktrees/run3-reconcile-hotfix-f95696ecc001/index` from root:root back to the invoking operator if and only if its path/owner/mode match the recorded defect. The helper must prove source preflight, root:root 0711 shared socket parent, intended same-socket access plus cross-socket denial, stable reconciliation controller, policy equivalence, active_projects=[research-engine], planned_projects_skipped=[padataset], mutation_performed=true, PADataset absence, and RUN3_RECONCILIATION_PLANE=PASS. Do not run the old race-hotfix helper again; do not change policy, bump registry_epoch, rerun the full migration, restage the token, or onboard PADataset.

## Remaining work

- Run 3 immediate: from a fresh clean detached worktree at exact SHA 8adfe21f553d4cf5c2d4ff3299d2ced611ec4fa1, run scripts/lambda_ci_reconciliation_socket_hotfix_v1.sh via sudo with the exact expected SHA. The operator wrapper may repair only the one proven stale root-owned old-worktree index before creating/removing worktrees. Require RECONCILIATION_SOCKET_HOTFIX_SOURCE_PREFLIGHT=PASS, SOCKET_PARENT_AND_GROUP_ISOLATION=PASS, terminal reconciliation receipt PASS, and RUN3_RECONCILIATION_PLANE=PASS.
- Run 3: checkpoint the accepted Git-driven reconciliation controller/root path; only then mark git_driven_project_reconciliation VALIDATED.
- Run 3: run research-engine CPU, gpu-small and at least one already-accepted model-eval regression through the generic installed path, with clean terminal receipts and zero residue/quarantine.
- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard PADataset by registry/manifest reconciliation only, then execute non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal research-engine/PADataset filesystem/process/cache isolation and verify zero controller/provisioner/runtime source changes during PADataset onboarding.
- Final: prove a third approved repository requires only registry + manifest + thin launcher binding and freeze the reusable operating contract.

## Blockers / gates

- Source repair is validated and merged, but the live host still has the old /run/workspace-ci parent contract and the stale root-owned index in the prior hotfix worktree. Apply only the validated socket hotfix from exact main 8adfe21f553d4cf5c2d4ff3299d2ced611ec4fa1; do not rerun the old helper.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
