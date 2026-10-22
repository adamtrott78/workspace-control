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

RUN 4 LIVE RECONCILIATION READBACK ONLY: read the reconciliation-controller last-success state and matching root receipt for fresh policy SHA 4151a152409f5912ec561350ad1080bb9d5c63fa (or a later policy-equivalent task-only main), require active_projects=[padataset,research-engine], planned_projects_skipped=[], mutation_performed=true, and terminal COMPLETED. Verify ci-padataset user/group, /srv/workspace-ci/padataset root/standard subroots, installed registry epoch 5 + ACTIVE PADataset manifest with exact workflow blobs, padataset CPU/GPU controller envs and enabled/active services, research-engine non-regression, zero pre-canary PADataset workspace/process/quarantine residue, and unchanged generic installed provisioner/runtime/reconciler blobs. Do not trigger PADataset CPU/GPU canaries until this host readback passes.

## Remaining work

- Run 4: bind PADataset CPU/GPU launcher workflow blobs, onboard PADataset by registry/manifest reconciliation only, then execute non-scientific CPU/GPU canaries.
- Run 4: prove reciprocal research-engine/PADataset filesystem/process/cache isolation and verify zero controller/provisioner/runtime source changes during PADataset onboarding.
- Final: prove a third approved repository requires only registry + manifest + thin launcher binding and freeze the reusable operating contract.

## Blockers / gates

- Live PADataset canaries remain gated on the read-only Lambda host reconciliation acceptance. Candidate PR #2 / abb797dc480bdb8764b0f377d4f4d5b8fce13f3f is prepared but untriggered.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-multirepo-research-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
