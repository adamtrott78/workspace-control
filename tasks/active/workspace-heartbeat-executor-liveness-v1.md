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

Measure and operationally distinguish ChatGPT browser/UI disconnect from continued server-side assistant execution, then replace indefinite stale Heartbeat ownership with a bounded, fail-closed executor lease and safe takeover protocol so a fresh chat can recover without guessing or restarting the Heartbeat server.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-heartbeat-executor-liveness-v1
- Remote checkpoint: ac4d321f056d5b9a30f6dce2f78dfb7617affb06
- Remote verified: true

## Next safe action

Do not change the live Heartbeat runtime yet. First finish/merge the pending v0.4.6 release PR #155 and its short-card, six-plus-update, and planned chat-handoff host gates. In parallel, freeze the executor-liveness state machine: separate last_model_touch_at from last_ui_seen_at; keep semantic heartbeats independent; define lease_expires_at and read-only status; permit takeover only after expiry; atomically supersede the old turn on takeover; make old-turn update/touch operations fail closed; and require a fresh lease assertion before post-wait mutating work. Then implement observation-only instrumentation on top of the accepted v0.4.6 source before enabling automatic takeover.

## Remaining work

- Finish the observability contract and exact state machine using current OpenAI documentation and live Heartbeat evidence.
- After v0.4.6 acceptance, implement observation-only model-touch and UI-seen timestamps plus read-only liveness status.
- Run a deliberate long-turn/frontend-interruption measurement and record the gap between UI last-seen and executor touches.
- Choose a bounded lease TTL from measured behavior rather than a guessed chat duration.
- Implement and validate atomic expired-owner takeover plus stale-writer fencing.
- Update the canonical Heartbeat procedure with safe takeover/recovery rules and preserve restart as rollback.

## Blockers / gates

- Implementation/deployment is gated on completion or durable acceptance of workspace-heartbeat v0.4.6 PR #155 so this work does not invalidate its remaining live visual/handoff acceptance.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-executor-liveness-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
