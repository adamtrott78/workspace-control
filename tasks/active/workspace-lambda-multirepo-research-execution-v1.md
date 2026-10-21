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
- Remote checkpoint: 9018d947202915ff6bed3762e0e0827a5482979e
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

VALIDATED RUN-3 BOOT RECOVERY READY. Keep the broken root services contained until execution. Create/reuse a fresh clean detached workspace-control worktree at exact SHA 9018d947202915ff6bed3762e0e0827a5482979e, then run `scripts/lambda_ci_run3_boot_recovery_hotfix_v1.sh` via sudo with WORKSPACE_CI_RUN3_BOOT_RECOVERY_EXPECTED_SHA set to that SHA. The helper must prove exact source and accepted installed-state preflights, install the tmpfiles boot contract, recover /run/workspace-ci as root:root 0711, enable+activate provisioner/reconciler/research-engine CPU+GPU controllers, preserve cross-socket denial, obtain the terminal reconciliation PASS with policy equivalence and PADataset skipped, and show zero restart-count increase across its stability window. Do not manually mkdir /run/workspace-ci, run older hotfix helpers, change policy, bump registry_epoch, restage the token, or onboard PADataset.

## Remaining work

- Run 3 immediate: from a fresh clean detached worktree at exact validated repair SHA 9018d947202915ff6bed3762e0e0827a5482979e, execute scripts/lambda_ci_run3_boot_recovery_hotfix_v1.sh via sudo with WORKSPACE_CI_RUN3_BOOT_RECOVERY_EXPECTED_SHA set to that SHA. Require source+installed-state preflights, boot socket isolation PASS, all intended services enabled+active+stable, terminal reconciliation receipt PASS, and RUN3_RECONCILIATION_PLANE=PASS.
- Run 3: checkpoint the accepted Git-driven reconciliation controller/root path; only then mark git_driven_project_reconciliation VALIDATED.
- Run 3: run research-engine CPU, gpu-small and at least one already-accepted model-eval regression through the generic installed path, with clean terminal receipts and zero residue/quarantine.
- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard PADataset by registry/manifest reconciliation only, then execute non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal research-engine/PADataset filesystem/process/cache isolation and verify zero controller/provisioner/runtime source changes during PADataset onboarding.
- Final: prove a third approved repository requires only registry + manifest + thin launcher binding and freeze the reusable operating contract.

## Blockers / gates

- Validated reboot recovery is ready but not yet applied to Lambda. Root provisioner/reconciler should remain stopped/contained until the exact-SHA recovery helper is run.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
