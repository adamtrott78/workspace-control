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
- Remote branch: checkpoint-heartbeat-liveness-mvp-acceptance
- Remote checkpoint: 04852fe2111143a7950ccbdb15f3ed13b95a7521
- Remote verified: true

## Next safe action

v0.4.7 observation-only MVP is merged and GitHub CI PASS. Keep live v0.4.6 running until explicit controlled host rollout; validate same-card executor/UI/progress indicators and interruption behavior with real field evidence. Do not enable automatic stale-owner takeover.

## Remaining work

- Host-deploy accepted v0.4.7 candidate only after verifying rollout/rollback plan, with v0.4.6 and v0.4.5 retained.
- Verify current-card freshness display and sizing during same-chat activity.
- Collect real ChatGPT frontend-interruption evidence and measure touch gaps; do not infer exact assistant death.
- Choose a measured lease TTL and any recovery/takeover semantics only in a separate approved phase.

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
