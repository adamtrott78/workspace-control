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
- Remote checkpoint: 35e6f451fe36f039b5f6461f7469f0eed1e79e43
- Remote verified: true

## Next safe action

RUN 4 FINAL HOST ACCEPTANCE: inspect the most recent padataset provisioner record for exact candidate abb797dc480bdb8764b0f377d4f4d5b8fce13f3f and workload gpu-ci; require COMPLETED, RUNNER_EXITED_CLEANLY/SUCCEEDED, runner/staging workspaces destroyed, CPU/GPU process cleanup true, no CUDA OOM/resource/disk pressure, and matching root runtime receipt. Require no padataset p5-* workspace residue, no ci-padataset processes, no padataset quarantine, stable padataset CPU/GPU controllers, and reciprocal filesystem denial between ci-padataset and /srv/workspace-ci/research-engine plus ci-research-engine and /srv/workspace-ci/padataset. Re-verify installed generic source blobs unchanged. If PASS, close padataset_second_project_pilot and proceed to third-project declarative proof/freeze.

## Remaining work

- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard PADataset by registry/manifest reconciliation only, then execute non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal research-engine/PADataset filesystem/process/cache isolation and verify zero controller/provisioner/runtime source changes during PADataset onboarding.
- Final: prove a third approved repository requires only registry + manifest + thin launcher binding and freeze the reusable operating contract.

## Blockers / gates

- PADataset CPU and GPU canaries are workflow PASS and CPU root cleanup is PASS. Final Run-4 acceptance is gated only on GPU root cleanup + reciprocal project isolation + zero residue/quarantine + controller stability.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
