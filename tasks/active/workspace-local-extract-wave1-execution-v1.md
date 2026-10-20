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
- Remote checkpoint: c595d442689a4ddb4061c01a923ff0297c34bddd
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 366f9585145ab539dc43c3c974dcb8625489a3e3
- Remote verified: true

## Next safe action

Cancel workflow run 39200075204 in GitHub. Once cancelled, ChatGPT will rerun job 117891019967 using the GitHub Actions rerun-job endpoint. Do not add another PR #131 issue comment or create a new workflow run.

## Remaining work

- User cancels workflow run 39200075204 only.
- ChatGPT verifies cancelled terminal state and re-runs job 117891019967 as attempt 2 of the same workflow run.
- Follow attempt 2 through actual nine-paper benchmark, artifact, root receipt, cleanup, and PROMISING/PARTIAL/REJECT classification.
- Checkpoint result into research-engine-local-extract-redesign-v1 and archive support tasks.

## Blockers / gates

- Existing run 39200075204 must be cancelled so its stuck prelaunch attempt becomes terminal; connector lacks cancel permission/action in this chat. After cancellation, ChatGPT can rerun the same workflow job through the connected GitHub action.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-local-extract-wave1-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
