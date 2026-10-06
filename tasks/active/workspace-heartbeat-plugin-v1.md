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

Provide reliable operator-visible progress for each substantial ChatGPT assistant response through one atomic turn-begin operation, explicit turn-scoped updates, and one self-refreshing rolling-three card, while retaining task-level history separately.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-heartbeat-turn-scoped-v044
- Remote checkpoint: bbb4f09fac1864196b62a3126803a11b233d01f4
- Remote verified: true

## Next safe action

Plugin boundary refresh for live host acceptance: because v0.4.4 is a breaking Heartbeat tool-schema release and field evidence since v0.2 shows delete/recreate is the most reliable way to force a fresh custom MCP connection, delete the existing Heartbeat plugin connection, recreate it against https://kabob-retool-unstopped.ngrok-free.dev/mcp, then start a brand-new conversation and run the two-turn v0.4.4 acceptance. Existing chats are intentionally unsupported and cannot be upgraded in place.

## Remaining work

- Deploy exact tested v0.4.4 SHA bbb4f09fac1864196b62a3126803a11b233d01f4 to a dedicated active runtime without deleting workspace-heartbeat-runtime-v043.
- Switch the managed heartbeat-up runtime target to v0.4.4 only after exact-startup verification; preserve a one-command rollback target to v0.4.3.
- Delete/recreate the custom Heartbeat plugin connection against the same public MCP endpoint for this breaking schema release, then start a brand-new conversation.
- Start a brand-new ChatGPT conversation so the v0.4.4 tool schema and live-v2 UI resource are loaded.
- Run live two-turn acceptance: turn A begin_turn + rolling updates; user sends another message; turn B begin_turn; verify A becomes superseded/static and B rolls independently.
- Verify stale turn_id rejection, cross-conversation writer denial, terminal done ownership release, sidebar task history, and no duplicate live cards.
- Only after live PASS mark v0.4.4 accepted, update heartbeat-up as the canonical operator entrypoint, merge PR #110, and archive the v0.4.3 runtime as rollback.

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
