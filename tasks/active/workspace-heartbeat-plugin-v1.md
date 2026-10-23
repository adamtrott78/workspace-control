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

Preserve the accepted Workspace Heartbeat v0.4.5 lifecycle and semantic behavior while correcting live-card iframe sizing so short turns do not leave large blank transcript gaps.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-heartbeat-v046-intrinsic-resize
- Remote checkpoint: 3121953748acd42e792307c51f24e518c1443446
- Remote verified: true

## Next safe action

Finish the remaining live-host gates. First confirm the short live-v5 card hugs one/two updates with no blank transcript gap. Then run the six-plus-update regression for grow-through-five/scroll-from-six. Finally perform one planned chat-to-chat handoff: synchronize durable task state, make terminal heartbeat_update(..., state="done") the outgoing chat's final Heartbeat operation, and prove a fresh receiving chat can call heartbeat_begin_turn on the same real task_id without a server restart. If all three host gates pass, record evidence, mark the v0.4.6 stage VALIDATED/task COMPLETE, merge PR #155, verify post-merge main, preserve the v0.4.5 rollback, and stop.

## Remaining work

- Refresh/recreate Heartbeat if live-v5 is not loaded. Close active turns with done first where practical; if a stale pre-refresh owner blocks a real durable task ID, coordinate a Heartbeat-server-only restart to clear volatile ownership and retry the original task ID.
- Run short-turn live-v5 host acceptance: one- and two-update cards must hug intrinsic content with no giant blank transcript gap.
- Run long-turn regression acceptance: six updates must grow naturally through five and then scroll internally at approximately the five-update height.
- Validate one planned chat-to-chat handoff: outgoing chat synchronizes durable handoff state, sends terminal Heartbeat done, and a fresh receiving chat begins the same task_id without a server restart.
- After host PASS, merge PR #155, mark v0.4.6 accepted/COMPLETE, preserve v0.4.5 rollback, and stop.

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
