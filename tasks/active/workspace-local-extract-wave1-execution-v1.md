<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-local-extract-wave1-execution-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-local-extract-wave1-execution-v1
- Title: Trusted Lambda route for Local EXTRACT Wave 1
- Status: VALIDATING
- Capsule schema: v2

## Goal

Expose exactly the merged research-engine Local EXTRACT Wave 1 workflow to the already-accepted two-A4500 Qwen3.5 execution envelope, install that exact route on Lambda, execute one bounded nine-paper benchmark, and retire the route owner after final receipt/cleanup evidence. This task does not own EXTRACT scientific design or production routing.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: d5bc8bf6bc772547f4b2edb50f7595cc7e6edaac
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Read-only final host acceptance for request 7cdcb708-9ba9-511f-a689-13d8469db1da: inspect durable state + root receipt, verify zero residue/quarantine and destroyed runner/staging paths. Do not rerun the benchmark; Wave 1 scientific decision is already REJECT.

## Remaining work

- Read and verify the final root receipt and durable provisioner state for request 7cdcb708-9ba9-511f-a689-13d8469db1da.
- Require terminal success, exact model/runtime/two-GPU postverification, cleanup/postverify PASS, destroyed job/staging workspaces, zero project CPU/GPU residue, and no lane quarantine.
- Record final scientific disposition REJECT in research-engine-local-extract-redesign-v1 with the exact benchmark evidence.
- Archive runtime/provisioner/controller compatibility support tasks and this execution task after final acceptance.

## Blockers / gates

- Final root receipt gate only: verify /srv/workspace-ci/research-engine/logs/p5-7cdcb708-9ba9-511f-a689-13d8469db1da-receipt.json, terminal provisioner state, destroyed runner/staging workspaces, zero ci-research-engine CPU/GPU residue, and no gpu-heavy quarantine.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
