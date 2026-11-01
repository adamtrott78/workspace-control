<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-shell-mcp-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-shell-mcp-v1
- Title: Workspace Shell MCP v1
- Status: COMPLETE
- Capsule schema: v2

## Goal

Give ChatGPT durable, auditable, least-privilege command-execution access to the Lambda workspace through a separate private MCP/plugin so workspace-control tasks can execute and inspect bounded shell operations directly without using the operator as a copy/paste terminal relay, while preserving explicit provenance, credential isolation, rollback boundaries, and separately auditable privileged authority.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-shell-mcp-v1-current-main
- Remote checkpoint: 01a95b61410e2f427b9885a19e6a0b9c5ee60a38
- Remote verified: true

## Next safe action

TASK COMPLETE. Workspace Shell v1 is live-accepted at installed execution/authority SHA 01a95b61410e2f427b9885a19e6a0b9c5ee60a38 with bounded Git/validation execution, durable receipts, fail-closed path/argv/privileged-helper denials, and all four services active while remaining boot-disabled. Resume the separate parked GitRunner migration task at padataset-cpu-public-v1 under its own fresh exact canary authority; do not reuse Workspace Shell task authority or alter the empty privileged-helper trust stores.

## Remaining work

- None.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-mcp-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
