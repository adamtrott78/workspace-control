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

SOCKET HOTFIX PRECHECK FAILED CLOSED; do not rerun it yet. Run the bounded read-only provisioner/control-plane diagnostic: capture workspace-ci-provisioner.service ActiveState/SubState/Result/ExecMainStatus/NRestarts/start+exit timestamps and recent journal; inspect /run/workspace-ci and provisioner.sock ownership/mode/type; hash the installed provisioner service script; capture workspace-ci-reconciler.service and research-engine CPU/GPU controller states; confirm workspace-ci-reconcile-controller.service remains stopped. Do not start/restart services, mutate /run/workspace-ci, rerun the socket hotfix, change policy, bump registry_epoch, restage the token, or onboard PADataset.

## Remaining work

- Run 3 immediate: perform read-only diagnostics of workspace-ci-provisioner.service and the required generic control-plane services, including systemd state/result/restart timestamps, provisioner journal, /run/workspace-ci parent and provisioner.sock state, installed provisioner blob, and research-engine CPU/GPU controller states. Do not start/restart anything until the cause of provisioner inactivity is known.
- Run 3: checkpoint the accepted Git-driven reconciliation controller/root path; only then mark git_driven_project_reconciliation VALIDATED.
- Run 3: run research-engine CPU, gpu-small and at least one already-accepted model-eval regression through the generic installed path, with clean terminal receipts and zero residue/quarantine.
- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard PADataset by registry/manifest reconciliation only, then execute non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal research-engine/PADataset filesystem/process/cache isolation and verify zero controller/provisioner/runtime source changes during PADataset onboarding.
- Final: prove a third approved repository requires only registry + manifest + thin launcher binding and freeze the reusable operating contract.

## Blockers / gates

- The validated socket hotfix remains unapplied because its pre-mutation prerequisite check found workspace-ci-provisioner.service inactive. Diagnose the provisioner and the other required generic control-plane services read-only before any restart or hotfix rerun.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
