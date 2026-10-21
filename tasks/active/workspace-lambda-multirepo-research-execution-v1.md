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

VALIDATE RESPONSE-LIVENESS REPAIR FIRST. Review/validate branch fix-reconcile-response-liveness-run3: 120s root-response budget, in-process TRANSIENT_ERROR retry semantics, nonfatal root BrokenPipe/ConnectionReset handling after receipt persistence, recovery-helper promotion of the new controller blob, widened bounded receipt wait, exact-source manifest updates, and focused regression tests. Require full repository validation PASS before any host mutation. Keep all affected services disabled/contained. Do not rerun prior helpers, delete the existing root COMPLETED receipt, change policy, bump registry_epoch, restage the token, or onboard PADataset.

## Remaining work

- Run 3 immediate: validate and merge the reconciliation response-liveness repair. Require task contracts, Python regression, pinned Go controller validation, and full integration PASS. Only then rerun the exact bounded boot-recovery helper from the new validated merge; root should replay the existing COMPLETED receipt without reapplying.
- Run 3: checkpoint the accepted Git-driven reconciliation controller/root path; only then mark git_driven_project_reconciliation VALIDATED.
- Run 3: run research-engine CPU, gpu-small and at least one already-accepted model-eval regression through the generic installed path, with clean terminal receipts and zero residue/quarantine.
- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard PADataset by registry/manifest reconciliation only, then execute non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal research-engine/PADataset filesystem/process/cache isolation and verify zero controller/provisioner/runtime source changes during PADataset onboarding.
- Final: prove a third approved repository requires only registry + manifest + thin launcher binding and freeze the reusable operating contract.

## Blockers / gates

- Root reconciliation correctness is already proven by the persistent COMPLETED receipt, but controller acknowledgement/liveness is not yet validated. Response-liveness repair is staged on fix-reconcile-response-liveness-run3 and must pass the full repository validation tier before live recovery is retried.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
