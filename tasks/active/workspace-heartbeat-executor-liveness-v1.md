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

## Current validated state

- v0.4.7 live on Lambda: PASS
- Node v20.20.2 plugin tests: 27/27 PASS
- Isolated :8788 startup: PASS
- Managed :8787 and public ngrok health: PASS
- v0.4.6 rollback preserved: PASS
- ChatGPT refreshed tool surface exposes heartbeat_touch: PASS
- Live same-card server/executor/semantic signal separation: PASS
- Real frontend-interruption persistence: PENDING
- Automatic stale-owner takeover: DISABLED / DEFERRED

## Field evidence

During a live v0.4.7 turn, silent heartbeat_touch calls were interleaved with ordinary GitHub work. The operator directly observed Executor freshness updating while Semantic progress remained unchanged. After touches stopped, Card/server polling remained fresh while Executor and Semantic ages advanced. Touches did not add semantic Heartbeat history.

## Next safe action

Run a deliberate long-turn field test. If ChatGPT reports `Connection interrupted`, do not press Stop. Observe whether the already-mounted card continues to show fresh Card/server polling and/or Executor touches independently of Semantic progress, and record the measured executor-touch gaps.

Do not enable automatic stale-owner takeover or choose a lease TTL until real interruption evidence exists.

## Remaining work

- Collect one real frontend-interruption observation.
- Measure executor-touch gaps during/around the interruption.
- Decide any TTL/recovery semantics only in a later approved phase.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-executor-liveness-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
