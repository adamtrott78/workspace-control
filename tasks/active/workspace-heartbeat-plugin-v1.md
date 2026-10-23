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

Preserve the accepted Workspace Heartbeat v0.4.5 lifecycle and semantic behavior while correcting live-card iframe sizing so short turns do not leave large blank transcript gaps.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-heartbeat-v046-current-main-restage
- Remote checkpoint: 050198002dfcf01c2520871d08b858bf43072547
- Remote verified: true

## Next safe action

v0.4.6 accepted and merged at cd396157d7e3e5c3f955c15e41bebba501057693; preserve v0.4.5 rollback. Continue separate observation-only executor-liveness v0.4.7 candidate; do not enable automatic takeover.

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
