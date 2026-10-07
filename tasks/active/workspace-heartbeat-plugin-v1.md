<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-heartbeat-plugin-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-heartbeat-plugin-v1
- Title: Workspace Heartbeat MCP Plugin v1
- Status: VALIDATING
- Capsule schema: v2

## Goal

Provide reliable operator-visible progress for each substantial ChatGPT assistant response through one atomic turn-begin operation, explicit turn-scoped updates, semantic-delta-first cadence, and one self-refreshing card that preserves the full bounded current-turn semantic history while retaining task-level history separately.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-heartbeat-v045-full-turn-history
- Remote checkpoint: 10226c1f87b05e479ee4f5e0115139dd7113aa8b
- Remote verified: true

## Next safe action

Run the exact Lambda Node 20/npm and isolated-startup gate for v0.4.5 implementation git:10226c1f87b05e479ee4f5e0115139dd7113aa8b while leaving the live v0.4.4 runtime on port 8787 untouched.

## Remaining work

- Run Workspace Control Validation for the exact v0.4.5 candidate head.
- Run exact Node 20 npm test and isolated startup smoke on Lambda without disturbing the live v0.4.4 runtime.
- Cut over the managed Heartbeat runtime only after the exact isolated gate passes, preserving v0.4.4 rollback.
- Refresh/recreate the custom Heartbeat plugin connection as needed for the output-schema/UI resource change and verify the v0.4.5 tool surface.
- Run live host acceptance with at least five semantic updates in one assistant response, verify the full scrollable current-turn chain, then verify next-turn supersession/isolation.
- Only after live PASS merge the v0.4.5 release PR and mark this stage VALIDATED/COMPLETE.

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
