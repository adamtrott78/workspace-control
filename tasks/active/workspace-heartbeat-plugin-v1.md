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
- Remote checkpoint: f7d079534fd1359bdbc103fc8a180a24b74ade89
- Remote verified: true

## Next safe action

Validate exact corrected live-v4 candidate with synchronous bridge-active `ui/notifications/size-changed` reporting (no resize timer). If npm tests pass on Lambda, restart the managed v0.4.5 runtime and refresh ChatGPT once for the five-update visual smoke.

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
