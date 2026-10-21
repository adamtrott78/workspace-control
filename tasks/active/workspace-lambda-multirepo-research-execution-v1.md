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

ACCEPTANCE ATTEMPT FAILED CLOSED; do not rerun the hotfix helper yet. First run the bounded read-only diagnostic block that checks workspace-ci-reconcile-controller.service state, workspace-ci-reconciler.service state, last-success.json/last-rejected.json, recent journals for both services, installed poller and pre-hotfix backup hashes, and ownership/mode of the detached hotfix worktree metadata including `.git/worktrees/run3-reconcile-hotfix-f95696ecc001/index`. The wrapper's previous clean-worktree check is known defective because it masked a failing `git status`; do not reuse that check. Do not change policy, bump registry_epoch, rerun the full migration, restage the token, or onboard PADataset.

## Remaining work

- Run 3 immediate: perform read-only diagnostics for the failed reconciliation-plane acceptance: verify controller stopped state/restart count, inspect last-success/last-rejected, controller and root-reconciler journals, installed poller and backup hashes, and worktree metadata/index ownership. Repair only the proven worktree/control-plane defect, then revalidate before any acceptance rerun.
- Run 3: checkpoint the accepted Git-driven reconciliation controller/root path; only then mark git_driven_project_reconciliation VALIDATED.
- Run 3: run research-engine CPU, gpu-small and at least one already-accepted model-eval regression through the generic installed path, with clean terminal receipts and zero residue/quarantine.
- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard PADataset by registry/manifest reconciliation only, then execute non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal research-engine/PADataset filesystem/process/cache isolation and verify zero controller/provisioner/runtime source changes during PADataset onboarding.
- Final: prove a third approved repository requires only registry + manifest + thin launcher binding and freeze the reusable operating contract.

## Blockers / gates

- Run-3 reconciliation-plane acceptance failed closed after credential PASS. Two issues require read-only diagnosis before any rerun: operator worktree metadata index permission drift caused `git status` to fail (and the wrapper masked it), and the controller produced no last-success receipt after HOTFIX_SOURCE_BLOB_PREFLIGHT=PASS. Inspect controller/root-reconciler journals, last-success/last-rejected state, installed poller/backup hashes, and exact worktree metadata ownership. Do not rerun activation yet.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
