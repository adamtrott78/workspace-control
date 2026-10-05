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

Build and validate a minimal MCP heartbeat tool plus ChatGPT conversation-panel UI so long-running workspace-control tasks can publish natural-language progress through a real tool call into one continuously updating side panel.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: heartbeat-v2-smoke-checkpoint
- Remote checkpoint: ff9347f347540fbe0f2a20b8b5106e80dc4572e5
- Remote verified: true

## Next safe action

Do not redesign transport based on the observation that a 15+ minute research turn emitted only two heartbeats. First finish/deploy v0.3.1, whose purpose is to eliminate all automatic background heartbeat_get traffic. Then run one genuine heartbeat_update to prove event-driven delivery. Separately audit the research chat's tool-call cadence: if more than three non-heartbeat tool operations occurred between the two visible heartbeat updates, treat that as an executor lease-compliance defect rather than a UI/transport defect.

## Remaining work

- Validate/deploy the final event-driven-only v0.3.1 heartbeat panel once the unrelated research-engine task-contract failure on workspace-control main is repaired or no longer blocks PR validation.
- After v0.3.1 is mounted, confirm an idle open panel produces no recurring MCP traffic and that a genuine heartbeat_update still appears promptly.
- Then audit executor cadence separately: during a long research turn, compare heartbeat_update events with non-heartbeat tool operations and verify the required heartbeat-before-fourth-tool lease is being followed.
- Do not add polling back merely because heartbeats are sparse; sparse model updates and background transport traffic are separate concerns.
- Close the heartbeat task only after event-driven delivery availability and executor heartbeat cadence are both accepted.

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
