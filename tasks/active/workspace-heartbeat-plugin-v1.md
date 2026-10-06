<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-heartbeat-plugin-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-heartbeat-plugin-v1
- Title: Workspace Heartbeat MCP Plugin v1
- Status: VALIDATING
- Current stage: in_chat_single_update_cards
- Exact v0.4 source: `cf1b9b645274dbc6945f0c2354694e554236edb1`
- Branch: `heartbeat-v2-smoke-checkpoint`
- PR: #69

## Current v0.4 design

- `heartbeat_update` renders through a dedicated in-chat update-card resource.
- Each update result contains only the newest `heartbeat`.
- `heartbeat_get` remains the separate optional history/sidebar surface with heartbeat/history/timeline.
- Update-card URI: `ui://workspace-heartbeat/update-card-v1.html`
- History/sidebar URI: `ui://workspace-heartbeat/panel-v7.html`
- The prior mounted-sidebar live-refresh problem is no longer the primary acceptance target.

## Validation state

- Exact v0.4 source shape: PASS.
- Repository-wide CI run `37396702037` did not reach heartbeat tests; it failed first on unrelated schema-invalid `research-engine-local-document-pipeline-v1.json`.
- Live v0.4 update-card smoke: NOT_RUN.

## Next safe action

Deploy exact Workspace Heartbeat v0.4.0 head cf1b9b645274dbc6945f0c2354694e554236edb1 to the isolated Lambda runtime, run local tests, refresh the custom plugin, and perform the single-message in-chat card smoke. If each heartbeat_update shows only its newest message and a fresh chat starts visually clean, checkpoint/close heartbeat without reopening sidebar-live-refresh work, then transfer ownership to the Lambda/GitHub tooling optimization child task.

## Remaining work

- Deploy exact heartbeat v0.4.0 head cf1b9b645274dbc6945f0c2354694e554236edb1 to the isolated Lambda heartbeat runtime and run local npm tests.
- Refresh/recreate the custom Workspace Heartbeat plugin if needed so update-card-v1.html/panel-v7.html metadata is loaded.
- During ordinary long-running work, verify each heartbeat_update renders one in-chat card containing only that newest message; prior heartbeat contents must not be replayed into the new card.
- Verify a fresh chat starts with no inherited update-card history.
- Keep heartbeat_get as optional history/sidebar; do not block acceptance on real-time mounted-sidebar refresh if update-card delivery is reliable.
- After v0.4 live acceptance, checkpoint/close the heartbeat side project and transfer attention to tasks/active/workspace-lambda-github-tooling-optimization-v1.json.

## Related post-heartbeat task

After heartbeat v0.4 is accepted, transfer attention to:

`tasks/active/workspace-lambda-github-tooling-optimization-v1.json`

Branch:

`workspace-lambda-github-tooling-optimization-v1`

Durable initialization head:

`7c5afaa48f4b5b51b0594f6db49e0bb91da5d6a6`

That optimization task is a child of the existing authoritative runner pilot `workspace-lambda-self-hosted-execution-v1`; it must rehydrate the parent P3/P4/P5 state before mutation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/workspace-heartbeat-plugin-v1.json`

Start from the normal workspace-control root route.

Treat the authoritative JSON capsule, synchronized Markdown handoff, exact branch state, and live Lambda evidence as the complete handoff.

First finish the v0.4 single-message in-chat card smoke. Do not reopen sidebar-live-refresh experimentation unless the v0.4 card path itself fails.

After v0.4 is accepted and heartbeat is checkpointed/closed, transfer to:

`tasks/active/workspace-lambda-github-tooling-optimization-v1.json`

Before optimizing Lambda/GitHub tooling, also rehydrate:

`tasks/active/workspace-lambda-self-hosted-execution-v1.json`

because its P3/P4/P5 state may have advanced independently.

Do not rely on prior chat prose.
