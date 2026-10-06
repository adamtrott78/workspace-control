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
- Remote checkpoint: bdfed66f59df69fffded0a2fa6d7ed1cb73458d0
- Remote verified: true

## Next safe action

Validate the exact fresh v0.4.4 release branch with Node 20: run node --check server.js and npm test from plugins/workspace-heartbeat. Do not change the live v0.4.3 runtime unless those gates pass.

## Remaining work

- Run node --check server.js and the complete npm test suite from the exact fresh v0.4.4 release branch on Lambda.
- If tests PASS, deploy v0.4.4 to an isolated runtime path while preserving workspace-heartbeat-runtime-v043 as rollback.
- Refresh the existing custom plugin connection instead of deleting/recreating it, then start a brand-new conversation so v0.4.4 schemas/UI are loaded.
- Run a multi-turn live acceptance: assistant turn A begins once and rolls updates; after the next user message, turn B begins once; turn A becomes superseded/static and turn B rolls independently.
- Verify stale turn_id rejection, cross-conversation active-writer denial, done ownership release, task-level sidebar history, and no duplicate live cards.
- Only after live PASS update heartbeat-up to the accepted runtime target, promote v0.4.4 docs from candidate to accepted, and merge the release PR.

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
