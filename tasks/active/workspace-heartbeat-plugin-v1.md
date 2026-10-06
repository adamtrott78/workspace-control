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

Build and validate a minimal MCP heartbeat tool plus ChatGPT conversation-panel UI so long-running workspace-control tasks can publish natural-language progress through a real tool call into one continuously updating side panel.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: heartbeat-v2-smoke-checkpoint
- Remote checkpoint: fd615356972cbe1d306cca793c387badf2f7168a
- Remote verified: true

## Next safe action

Validate and deploy Workspace Heartbeat v0.4.0. The primary live test is now the in-chat surface: each heartbeat_update must render exactly one compact card containing only that newest heartbeat, with no replayed history/timeline; a fresh chat must start visually clean. Keep heartbeat_get as the optional history/sidebar surface. Separately, treat long reasoning after an already-resolved external dependency as an executor-stall/heartbeat-cadence issue rather than a UI transport issue.

## Remaining work

- Validate the final Workspace Heartbeat v0.4.0 PR head.
- Deploy the exact validated v0.4.0 head/canonical merge to the Lambda heartbeat runtime and recreate/refresh the plugin.
- In a long-running research chat, verify each heartbeat_update creates one compact in-chat card containing only that heartbeat.
- Start a fresh chat and verify new heartbeat cards do not replay prior chat heartbeat contents.
- Use heartbeat_get only when explicit history/sidebar inspection is wanted; mounted sidebar live refresh is no longer the primary acceptance path.
- Separately investigate executor stalls when an external dependency resolves but the model remains in a long reasoning loop without emitting a state-change heartbeat.

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
