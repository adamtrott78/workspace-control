<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable archived view.

Authoritative capsule: tasks/archive/workspace-lambda-multirepo-research-execution-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-lambda-multirepo-research-execution-v1
- Title: Workspace Lambda Multi-Repository Research Execution v1
- Status: COMPLETE
- Capsule schema: v2
- Final stage: cross_project_isolation_and_reuse_acceptance

## Goal

Generalize the accepted GitHub-to-Lambda execution substrate from a research-engine-specific pilot into a reusable, fail-closed, manifest-driven research compute control plane that can execute bounded candidate code from research-engine, PADataset, and future explicitly authorized research repositories without per-task controller/provisioner/runtime patches or routine human SSH/sudo intervention.

## Final disposition

Task complete. The reusable GitHub-to-Lambda multi-repository research-compute control plane is accepted for research-engine and PADataset, with live reciprocal isolation and clean CPU/GPU receipts. A third-project executable proof confirms that ordinary future project onboarding requires only thin launcher workflows, exact workflow-blob binding, a registry entry, a schema-v2 project manifest, existing accepted execution contracts, trusted reconciliation, and bounded canary acceptance. Do not reopen controller/provisioner/runtime authority for ordinary onboarding. Any new capability not covered by an accepted execution contract, project removal, credential-authority redesign, or broader privileged surface must start as a separate reviewed workspace-control task.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 5179ebf43c67960254d8542ad4ce1a03c72480ed
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 35e6f451fe36f039b5f6461f7469f0eed1e79e43
- Remote verified: true

## Remaining work

- None.

## Blockers / gates

- None.

## Archived task

This durable task is complete. Future ordinary project onboarding should follow `architecture/lambda-ci-reusable-research-compute-contract.v1.md` and should not replay this task's accepted migration or runtime gates.
