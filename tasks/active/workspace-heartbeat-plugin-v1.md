<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-heartbeat-plugin-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-heartbeat-plugin-v1
- Title: Workspace Heartbeat MCP Plugin v1
- Status: BLOCKED_EVIDENCE
- Capsule schema: v2

## Goal

Build and validate a minimal MCP heartbeat tool plus ChatGPT conversation-panel UI so long-running workspace-control tasks can publish natural-language progress through a real tool call into one continuously updating side panel.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: heartbeat-v2-smoke-checkpoint
- Remote checkpoint: fd615356972cbe1d306cca793c387badf2f7168a
- Remote verified: true

## Next safe action

Do not change heartbeat source further. Wait for the owning research chat to restore a schema-valid research-engine-local-document-pipeline-v1 capsule on workspace-control main, then rerun PR #69 validation on the unchanged v0.3.3 head. Merge/deploy only after heartbeat validation actually runs and passes.

## Remaining work

- Wait for the owning research chat to restore schema-valid research-engine-local-document-pipeline-v1 state; do not mutate that concurrent task here.
- Rerun PR #69 validation on unchanged heartbeat v0.3.3.
- After a real heartbeat validation pass, merge and deploy panel-v6.html.
- Verify mounted live refresh without close/reopen, idle quietness, and cross-task timeline continuity.
- Close the task only after those live checks pass.

## Blockers / gates

- PR #69 validation is blocked by an unrelated invalid research-engine-local-document-pipeline-v1 task capsule on current workspace-control main; CI exits during task-contract validation before heartbeat tests run.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-heartbeat-plugin-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
