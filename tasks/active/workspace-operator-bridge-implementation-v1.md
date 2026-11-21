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
- Remote checkpoint: dc3dff5ea00bc9a41be71bb79950115817fc364c
- Remote verified: true

## Next safe action

WINDOWS-ONLY HOTKEY VISUAL-CREATE SMOKE — implementation dc3dff5ea00bc9a41be71bb79950115817fc364c passed Workspace #3070 / Semantic #370 / Operator #643. Intended UX: after launch the dedicated Firefox profile remains visibly idle on exactly one about:blank/about:newtab; do NOT navigate that startup tab to ChatGPT. On one Ctrl+Space create/service press, create a fresh active https://chatgpt.com/?temporary-chat=true tab, request Firefox OS focus, then close only the exact unmanaged startup blank captured before creation; clipboard behavior remains the already-proven WORKSPACE_OPERATOR_SMOKE_PACKET_V1 write. NEXT ACTION: run wop smoke on the current bookkeeping tip with no manual Firefox/tab cleanup. Before Ctrl+Space require one blank tab. After Ctrl+Space require one Personalized Temporary Chat tab, no blank duplicate, managed Firefox foreground, and clipboard exactly WORKSPACE_OPERATOR_SMOKE_PACKET_V1. No automatic paste/typing/Enter/Send. Do not infer live Stage-12 authority from this local smoke.

## Remaining work

- live transport gate: after Workspace Shell semantic authority exists, prove exact-host Tailscale fake-worker transport before real-account use.
- impl_12: bounded real-account calibration with no DOM/content automation, no added browser permissions and no security workaround.
- impl_09: authoritative target-machine UX-09 performance/resource benchmark after real-account calibration.
- impl_13: explicit PROMOTE_V0/HOLD/REVISE production-readiness review.

## Blockers / gates

- The authoritative long-form UX-09 target benchmark remains intentionally SUSPENDED as an intermediate gate. It remains mandatory before impl_13 production readiness can pass.
- Real-account Stage-12 retry remains paused. Hotkey visual-create repair dc3dff5e… is 3/3 validated, but the operator must rerun the Windows-only smoke and empirically confirm idle blank -> Ctrl+Space fresh Temporary Chat open/focus -> startup blank closed, with exact clipboard packet. No new live retry authority exists.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
