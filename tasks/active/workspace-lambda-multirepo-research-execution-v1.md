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

REPOSITORY-SELECTION DEFECT IS PROVEN; keep workspace-ci-reconcile-controller.service stopped. Recreate the fine-grained GitHub PAT with resource owner `adamtrott78`, repository access `Only select repositories` -> `workspace-control`, and repository permissions `Contents: Read-only` plus `Actions: Read-only` only. Restage it with `sudo -u ci-reconciler /opt/workspace-ci/reconcile-controller/stage-pat`. Before restarting anything, rerun the repository-visibility diagnostic and require `authenticated_login=adamtrott78`, `workspace_control_visible_to_token=YES`, then rerun the five-endpoint capability probe and require five HTTP_200 results. Do not change reconciliation policy, bump registry_epoch, rerun the full migration, or onboard PADataset.

## Remaining work

- Run 3 immediate: recreate the dedicated fine-grained reconciliation token with resource owner adamtrott78, explicit repository access to workspace-control, and only Contents read + Actions read; restage it, require workspace_control_visible_to_token=YES plus all five capability probes HTTP_200, then rerun the validated reconciliation-plane acceptance without a registry bump.
- Run 3: checkpoint the accepted Git-driven reconciliation controller/root path; only then mark git_driven_project_reconciliation VALIDATED.
- Run 3: run research-engine CPU, gpu-small and at least one already-accepted model-eval regression through the generic installed path, with clean terminal receipts and zero residue/quarantine.
- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard PADataset by registry/manifest reconciliation only, then execute non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal research-engine/PADataset filesystem/process/cache isolation and verify zero controller/provisioner/runtime source changes during PADataset onboarding.
- Final: prove a third approved repository requires only registry + manifest + thin launcher binding and freeze the reusable operating contract.

## Blockers / gates

- The freshly staged reconciliation token authenticates as adamtrott78 but `workspace-control` is not in its accessible private-repository set (`workspace_control_visible_to_token=NO`). The reconciliation controller remains intentionally stopped. Recreate the fine-grained PAT with resource owner adamtrott78 and explicit repository selection `workspace-control`; do not bump the registry, rerun root migration, or touch PADataset.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
