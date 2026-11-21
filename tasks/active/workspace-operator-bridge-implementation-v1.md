<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-operator-bridge-implementation-v1
- Title: Workspace Operator Bridge Implementation v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Implement the UX-13-frozen human-operated Chat Instant bridge as a staged, test-first Windows/Firefox system: .NET 10 helper, typed Native Messaging/named-pipe BrowserPort, least-privilege Firefox MV3 adapter, deterministic fake-worker simulator, recovery/fault closure, packaging/rollback, empirical performance/usability evidence, optional WebView2 comparison, and gated real-account calibration without changing the frozen manual Ctrl+V + Enter or authority/security boundaries.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-semantic-execution-migration-v1
- Remote checkpoint: bfa6e5dd658e6d91e8699e396e888058913e20d0
- Remote verified: true

## Next safe action

WINDOWS-ONLY HUMAN-ENTER HANDOFF SMOKE — bfa6e5dd658e6d91e8699e396e888058913e20d0 passed Workspace #3074 / Semantic #374 / Operator #647. Existing visual loop is already confirmed working: clean blank startup, first Ctrl+Space creates/focuses fresh Personalized Temporary Chat, closes startup blank and loads clipboard. NEW GATE: after preparation, do not advance/minimize until a plain Enter keypress is observed while the captured worker Firefox window is foreground. A premature second Ctrl+Space must refocus Firefox and show the no-Enter-confirmation alert; it must not dispatch or minimize. After the human pastes the prompt and presses plain Enter, the next Ctrl+Space may resume normal dispatch; with no remaining smoke action it should minimize and report nothing needs service. This confirms only the human Enter event, not ChatGPT execution/output. No automatic typing/paste/Enter/Send and no live Stage-12 authority.

## Remaining work

- live transport gate: after Workspace Shell semantic authority exists, prove exact-host Tailscale fake-worker transport before real-account use.
- impl_12: bounded real-account calibration with no DOM/content automation, no added browser permissions and no security workaround.
- impl_09: authoritative target-machine UX-09 performance/resource benchmark after real-account calibration.
- impl_13: explicit PROMOTE_V0/HOLD/REVISE production-readiness review.

## Blockers / gates

- The authoritative long-form UX-09 target benchmark remains intentionally SUSPENDED as an intermediate gate. It remains mandatory before impl_13 production readiness can pass.
- Real-account Stage-12 retry remains paused. Human-Enter gate bfa6e5dd… is 3/3 validated, but operator must run the Windows-only smoke and empirically prove: first Ctrl+Space prepares the worker; second Ctrl+Space before plain Enter alerts/refocuses without minimize/advance; plain Enter while prepared worker Firefox is foreground then unlocks the next Ctrl+Space. No new live retry authority exists.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
