<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-heartbeat-executor-liveness-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-heartbeat-executor-liveness-v1
- Title: Workspace Heartbeat Executor Liveness v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Give the operator, inside the existing Heartbeat card and without opening a new chat, an independent view of demonstrated assistant-executor liveness that remains useful when the ChatGPT website says connection interrupted. Keep semantic progress and executor activity separate, then use the same observation layer later for bounded stale-owner recovery.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-heartbeat-executor-liveness-mvp
- Remote checkpoint: cd396157d7e3e5c3f955c15e41bebba501057693
- Remote verified: true

## Next safe action

Validate observation-only v0.4.7 liveness branch workspace-heartbeat-executor-liveness-mvp. Keep semantic progress, executor touch, and app UI poll independent; no automatic stale-owner takeover. Deploy only after acceptance, then collect real interrupted-chat evidence.

## Remaining work

- Validate isolated v0.4.7 observation-only candidate with CI and regression tests.
- Inspect v0.4.7 UI card tests and merge only after successful validation.
- Do not deploy without explicit host validation; preserve v0.4.6 and v0.4.5 rollback.
- Observe a real frontend interruption and measure touch gaps before any TTL or takeover design.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-executor-liveness-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
