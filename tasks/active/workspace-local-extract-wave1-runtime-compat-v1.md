<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-local-extract-wave1-runtime-compat-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-local-extract-wave1-runtime-compat-v1
- Title: Local EXTRACT Wave 1 runtime compatibility
- Status: VALIDATING
- Capsule schema: v2

## Goal

Allow the already-authorized Local EXTRACT Wave 1 workload through the final privileged runtime workload gates without broadening gpu-heavy authority, then install the exact runtime fix and recover the existing benchmark request without issuing another trigger.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: c595d442689a4ddb4061c01a923ff0297c34bddd
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Have the user cancel only workflow run 39200075204. After it reaches completed/cancelled, ChatGPT must call the GitHub re-run-job action for job 117891019967, creating attempt 2 of the same workflow run. Do not post another /lambda-ci-local-extract-wave1 comment.

## Remaining work

- Cancel existing workflow run 39200075204 in GitHub; do not create a new workflow trigger/comment.
- After GitHub reports attempt 1 cancelled, use the GitHub Actions re-run-job API on job 117891019967 to create attempt 2 of the same workflow run.
- Follow the attempt-2 job through controller/provisioner/runtime execution and collect artifact/final root receipt.
- Close runtime/provisioner/controller children after successful execution acceptance.

## Blockers / gates

- GitHub attempt-1 cancellation gate: current run 39200075204/job 117891019967 remains queued/assigned with no recoverable JobAssigned metadata. The connector can re-run a completed/cancelled job but cannot cancel this queued run, so one user cancellation of the existing run is required.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-runtime-compat-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
