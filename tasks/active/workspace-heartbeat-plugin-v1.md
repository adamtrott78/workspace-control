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
- Remote branch: workspace-heartbeat-v045-full-turn-history-r2
- Remote checkpoint: c91ee09f6594e1e76134159b211fe224a8409b6b
- Remote verified: true

## Next safe action

Refresh/recreate the custom Heartbeat plugin connection and fully refresh ChatGPT so live-v4 is loaded, then run one visual smoke: updates 1-5 must grow the card naturally and update 6+ must scroll within the measured five-entry height. After PASS, merge PR #139 and mark v0.4.5 COMPLETE.

## Remaining work

- Refresh/recreate the custom Heartbeat plugin connection and fully refresh ChatGPT so the cache-busted live-v4 resource is loaded.
- Run visual host acceptance: updates 1-5 grow naturally with no internal scrolling; update 6+ uses a five-entry-tall internal scroller; prior-turn isolation and supersession remain correct.
- After live PASS, merge PR #139 and mark v0.4.5 accepted/COMPLETE.

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
