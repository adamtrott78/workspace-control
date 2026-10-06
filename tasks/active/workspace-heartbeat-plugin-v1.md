<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: `tasks/active/workspace-heartbeat-plugin-v1.json`

If this view disagrees with the JSON capsule or verified Git/runtime evidence,
trust the capsule plus verified evidence.

## Task

- ID: `workspace-heartbeat-plugin-v1`
- Status: **COMPLETE**
- Accepted design: Workspace Heartbeat **v0.4.3**
- Implementation checkpoint: `d7e692171c93f96adf7a70c6a1e514113a18075e`
- Branch: `heartbeat-v2-smoke-checkpoint`
- PR: #69
- Lambda runtime: `workspace-heartbeat-runtime-v043`

## Accepted operating contract

1. Start the Lambda heartbeat service with `heartbeat-up`.
2. During sustained ChatGPT work, write the first natural progress update with
   `heartbeat_update(task_id, message, state)`.
3. Call `heartbeat_open(task_id)` exactly once near the beginning.
4. Continue data-only `heartbeat_update` calls at meaningful state changes and
   before the fourth non-heartbeat tool operation.
5. Do not reopen/render the card. The existing iframe calls app-only
   `heartbeat_snapshot(task_id)` and keeps the same rolling-three card fresh.
6. Use `heartbeat_get(task_id)` only for explicit full task-local history.
7. Mark the final heartbeat `done` when the owning task actually completes.

`heartbeat_render` is retired. Native commentary is not the guaranteed
heartbeat delivery path.

## Live acceptance evidence — 2026-10-06

The user directly observed the same original card updating multiple times while
later GitHub/tool operations continued. The card rolled to the newest three
task-local heartbeats, changed to DONE, and required no second open/render call.

The user also verified the operator-local startup helper contains:

```text
DIR="/home/atrott/adamArchives/Adam/workspace-heartbeat-runtime-v043/plugins/workspace-heartbeat"
```

Therefore the normal operator startup command is simply:

```bash
heartbeat-up
```

Changing that runtime target requires fresh runtime and live-host validation.

## Closure

The heartbeat side project is complete. Resume:

`tasks/active/workspace-lambda-github-tooling-optimization-v1.json`

Do not reopen heartbeat design work absent a new functional regression or
explicitly authorized runtime change.
