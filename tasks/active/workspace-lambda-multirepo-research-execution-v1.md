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
- Remote checkpoint: a4a5e1a2afc004b484542d5a71746e6472154fdb
- Remote verified: true

## Next safe action

RUN 3 GITHUB REGRESSIONS PASS; HOST CLEANLINESS GATE ONLY. Execute one bounded read-only Lambda host acceptance block that selects the most recent provisioner records for candidate/workload tuples (f5ba827.../cpu-test, f5ba827.../gpu-small, 522430a.../model-eval-local-extract-wave1), requires COMPLETED plus clean nested runtime receipts, verifies zero research-engine process/workspace/transient-unit residue and no lane quarantine, proves all five control-plane services active without restart-count growth across a short stability window, and proves PADataset remains absent. Do not onboard PADataset until this gate is PASS.

## Remaining work

- Run 3 final regression gate: run the bounded read-only host acceptance block over the three just-completed research-engine executions. Require matching COMPLETED provisioner records, nested runtime result RUNNER_EXITED_CLEANLY / terminal_status SUCCEEDED, cleanup invariants, no p5-* job/staging directories, no ci-research-engine processes or transient units, no research-engine lane quarantine, all five control-plane services active with stable restart counts, and PADataset still absent.
- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard PADataset by registry/manifest reconciliation only, then execute non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal research-engine/PADataset filesystem/process/cache isolation and verify zero controller/provisioner/runtime source changes during PADataset onboarding.
- Final: prove a third approved repository requires only registry + manifest + thin launcher binding and freeze the reusable operating contract.

## Blockers / gates

- Run-3 research-engine GitHub/job-layer regressions are all PASS. Final Run-3 regression acceptance is gated only on one read-only Lambda host proof of terminal root receipts, zero residue/quarantine, stable services, and continued PADataset absence.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
