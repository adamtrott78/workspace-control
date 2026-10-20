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
- Remote branch: lambda-multirepo-run3-live-migration-v1
- Remote checkpoint: 61b350699882453a089ad2b73b9a5da2ed1574c3
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

Merge the exact validated Run-3 pre-mutation package (head 61b350699882453a089ad2b73b9a5da2ed1574c3), checkpoint the resulting canonical main SHA, then run only `WORKSPACE_CI_MULTIREPO_EXPECTED_SHA=<canonical-main-sha> sudo -E scripts/migrate_lambda_ci_multirepo_v1.sh` from that exact clean Lambda workspace-control checkout. Return the complete install receipt/output for inspection. Do not stage the ci-reconciler token, activate workspace-ci-reconcile-controller.service, trigger research-engine regressions, or touch PADataset until the migration receipt is accepted.

## Remaining work

- Run 3: design and execute one bounded root migration/install of the validated generic controller/provisioner/runtime/reconciliation substrate on Lambda.
- Run 3: preserve rollback to the accepted research-engine-specific installed state and prove controller/provisioner service health plus exact installed source/blob identities.
- Run 3: run research-engine CPU, gpu-small and at least one already-accepted model-eval regression through the generic installed path, with clean terminal receipts and zero residue/quarantine.
- Run 3: activate and prove the trusted Git-driven project reconciliation controller/root path; only after that may git_driven_project_reconciliation become VALIDATED.
- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard PADataset by registry/manifest reconciliation only, then execute non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal research-engine/PADataset filesystem/process/cache isolation and verify zero controller/provisioner/runtime source changes during PADataset onboarding.
- Final: prove a third approved repository requires only registry + manifest + thin launcher binding and freeze the reusable operating contract.

## Blockers / gates

- Human-only Run-3 root gate after merge: execute the exact one-time migration script on Lambda via sudo from the canonical merged workspace-control checkout. No authorized connector can substitute for this root host mutation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
