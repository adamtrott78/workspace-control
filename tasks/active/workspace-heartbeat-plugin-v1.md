<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-heartbeat-plugin-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-heartbeat-plugin-v1
- Title: Workspace Heartbeat MCP Plugin v1
- Status: COMPLETE
- Capsule schema: v2

## Goal

Provide reliable operator-visible progress for each substantial ChatGPT assistant response through one atomic turn-begin operation, explicit turn-scoped updates, and one self-refreshing rolling-three card, while retaining task-level history separately.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-heartbeat-turn-scoped-v044
- Remote checkpoint: bbb4f09fac1864196b62a3126803a11b233d01f4
- Remote verified: true

## Next safe action

Heartbeat v0.4.4 is complete and accepted. Resume the separate owning workspace/Lambda task. OPTIONAL DEFERRED FEATURE: if the user explicitly asks to show all current-turn Heartbeat updates, reopen this task only for the implementation-ready full-turn scrollable-card follow-up documented in notes; otherwise leave Heartbeat unchanged.

## Remaining work

- None.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-plugin-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
