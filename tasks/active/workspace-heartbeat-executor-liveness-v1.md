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
- Remote branch: workspace-heartbeat-executor-liveness-v1
- Remote checkpoint: ac4d321f056d5b9a30f6dce2f78dfb7617affb06
- Remote verified: true

## Next safe action

Finish Workspace Heartbeat v0.4.6 PR #155 host acceptance first. Use the already-live v0.4.6 candidate to confirm (1) short one/two-update cards hug intrinsic content with no giant blank gap, (2) six same-turn semantic updates preserve grow-through-five/scroll-from-six, and (3) one planned chat-to-chat handoff releases with terminal done and lets a receiving chat begin the same task ID without server restart. After PR #155 is merged, implement the observation-only same-card liveness layer: model-only heartbeat_touch, last_executor_touch_at, last_ui_seen_at, and a live-card status row. Do not enable automatic takeover or claim exact executor death.

## Remaining work

- Finish the three remaining v0.4.6 live-host gates and merge PR #155 without changing the liveness feature.
- On top of accepted v0.4.6, implement heartbeat_touch and independent executor/UI timestamps without changing semantic Heartbeat history.
- Add the same-card status row showing server/card connectivity, executor last-seen age/status, and semantic-progress age.
- Test that heartbeat_touch is cross-conversation/turn fenced, does not increment semantic sequence/history, and does not create/resize transcript UI.
- Run a deliberate frontend-interruption observation to measure how long executor touches continue after the website reports connection interruption.
- Only after measurement choose a lease TTL and consider stale-owner takeover.

## Blockers / gates

- Do not implement or deploy the liveness layer until Workspace Heartbeat v0.4.6 PR #155 passes its remaining short-card, six-plus-update, and planned handoff live-host gates and is durably merged.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-executor-liveness-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
