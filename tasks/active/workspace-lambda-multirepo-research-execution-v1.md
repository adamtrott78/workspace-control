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
- Remote checkpoint: 2b22af474791ff59cc9cb100f4bf3b939266fec2
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

Run 2 implementation only. Starting from the validated Run-1 architecture, remove research-engine/project/workload privilege constants from the generic controller/provisioner/runtime path: controller becomes required project+lane configuration with a generic strict display-claim parser; provisioner resolves project_id through the root registry and validates derived runner identity; privileged runtime enforces resolved execution-contract semantics rather than route names. Add focused migration, third-project, PADataset-public-boundary and negative tests. Also implement the reconciliation plane in disabled/non-live form. Do not install or restart Lambda services and do not mutate PADataset in Run 2.

## Remaining work

- Run 2: implement the frozen generic controller/provisioner/runtime changes and focused migration/adversarial tests; no live install yet.
- Run 2: implement the bounded reconciler/controller templates in disabled/non-live form and validate replay, derivation and privilege ceilings.
- Run 3: perform one bounded root migration/install of the generic substrate and prove all existing research-engine routes/regression identities remain accepted.
- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard via registry/manifest reconciliation only, and run non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal project-root/process/cache denial, zero residue/quarantine, and no controller/provisioner/runtime source changes during PADataset onboarding.
- Final: freeze the reusable operating contract and demonstrate a synthetic/real third project needs only registry + manifest + thin launcher bindings.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
