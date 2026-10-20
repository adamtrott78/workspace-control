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
- Remote branch: lambda-multirepo-research-execution-v1
- Remote checkpoint: 4d580661a27f151e70f778111a88579e54de1c71
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

Design the P6 multi-project contract before implementation. Replace fixed research-engine project/repository/scale-set/runner assumptions with a root-owned project registry; replace experiment-specific privileged workload-name gates with semantic resource/capability validation; design a trusted Git-driven reconciliation path so subsequent approved repository onboarding requires no routine human terminal. PADataset is the first second-project pilot and must onboard without controller/provisioner/runtime source changes.

## Remaining work

- Design the root-owned project registry, generic controller instance model, semantic runtime authorization, and Git-driven reconciliation mechanism.
- Implement and validate generic controller/provisioner/runtime behavior without changing existing research-engine scientific routing.
- Activate the generic control-plane implementation through one bounded root migration gate.
- Onboard PADataset through manifests/workflows only; no controller/provisioner/runtime source edits.
- Run PADataset CPU and GPU canaries and prove mutual research-engine/PADataset isolation.
- Freeze the reusable operating contract so future approved repositories/tasks need only project configuration and candidate code, not infrastructure surgery.

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
