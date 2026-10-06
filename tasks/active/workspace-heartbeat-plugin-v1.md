<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Authoritative capsule: `tasks/active/workspace-heartbeat-plugin-v1.json`

## Current state

- Status: **VALIDATING**
- Stage: `turn_scoped_implementation_v044`
- Release branch: `workspace-heartbeat-turn-scoped-v044`
- Base main: `7ad3f357e9ee75d9a01bb19a4bda062f0d59d801`
- Candidate branch head before this metadata commit: `1a18fac7dea77acd332f3d426314659fec6b0b73`
- Production rollback: v0.4.3
- Candidate: v0.4.4

## Contract

Every substantial assistant response starts with one
`heartbeat_begin_turn(task_id, message, state)`. It atomically supersedes the
prior turn, creates an opaque server `turn_id`, writes the first heartbeat, and
mounts the current-turn rolling-three card.

Later writes require:
`heartbeat_update(task_id, turn_id, message, state)`.

The app reads only `heartbeat_snapshot(task_id, turn_id)`. Superseded/completed
cards stop polling. `heartbeat_get(task_id)` remains explicit task history.

Conversation metadata is used only for one-writer ownership enforcement.
A terminal `done` releases the in-memory ownership lease.

## Validation

In-session V8 source/lifecycle harness: PASS.

Still required:
1. exact Node 20 `npm test`;
2. isolated v0.4.4 Lambda deployment;
3. plugin refresh and a **new conversation**;
4. live two-turn acceptance proving turn A freezes when turn B begins.

Do not replace v0.4.3 before those gates pass.
