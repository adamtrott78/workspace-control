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

Run exact Lambda npm test at git:c91ee09f6594e1e76134159b211fe224a8409b6b. Repository validation run 37690173953 is PASS. If all 26 plugin tests pass, restart the managed v0.4.5 runtime, verify local/public health, refresh the plugin/browser, and repeat the five-update visual smoke.

## Remaining work

- Allow PR #139 Workspace Control Validation to complete on the fresh current-main release branch.
- Refresh/recreate the custom Heartbeat plugin connection and perform a full browser refresh so ChatGPT loads the v0.4.5 tool metadata and live-v3 resource.
- Verify the effective tool/output surface includes bounded turn_history and the semantic-delta/10-tool guidance rather than the stale rolling-three/pre-fourth-tool metadata.
- Run live host acceptance with at least five semantic updates in one assistant response; verify all remain readable in one scrollable current-turn card, deliberate upward scroll is preserved, and the next assistant response supersedes/freezes the prior card.
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
