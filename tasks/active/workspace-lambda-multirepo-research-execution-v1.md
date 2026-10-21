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
- Remote checkpoint: f924f2bf45fbf05aa3f0dc2ea036354143834246
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

LATEST ATTEMPT STATE/JOURNAL DIAGNOSTIC COMPLETE: root receipt is intact, rollback restored accepted predecessor blobs, services are contained, but unit-scoped journals are empty. Do not rerun recovery yet. Run the bounded read-only broad-journal diagnostic across the current boot/system manager: journalctl -b since 18:30 filtered for workspace-ci, lambda_ci_reconcile_controller.py, lambda_ci_reconciler.py, Python tracebacks, systemd start/stop/failure messages; show journal boots/timezone/storage metadata and any relevant syslog forwarding. If this still yields no execution evidence, the next source change should be observability-only phase markers validated before a new live attempt. Do not delete receipts, change policy, bump registry_epoch, restage the token, or onboard PADataset.

## Remaining work

- Run 3 immediate: perform one broader read-only journal/manager diagnostic for the current boot. Query all journal entries matching workspace-ci service names, reconciliation executable names, systemd start/stop/failure messages, Python tracebacks, and the 18:30 onward window without relying only on `journalctl -u`; also print journald storage/timezone/boot metadata. If still no evidence, add validated phase-level controller observability before another live attempt rather than blind rerunning.
- Run 3: checkpoint the accepted Git-driven reconciliation controller/root path; only then mark git_driven_project_reconciliation VALIDATED.
- Run 3: run research-engine CPU, gpu-small and at least one already-accepted model-eval regression through the generic installed path, with clean terminal receipts and zero residue/quarantine.
- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard PADataset by registry/manifest reconciliation only, then execute non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal research-engine/PADataset filesystem/process/cache isolation and verify zero controller/provisioner/runtime source changes during PADataset onboarding.
- Final: prove a third approved repository requires only registry + manifest + thin launcher binding and freeze the reusable operating contract.

## Blockers / gates

- Second replay post-attempt state is contained and the authoritative root receipt remains valid, but unit-scoped journald returned no entries for the latest attempt. Before another mutation, broaden read-only observability to the entire current boot/systemd manager and executable identifiers to determine whether service starts/logs were recorded outside the `journalctl -u` view.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
