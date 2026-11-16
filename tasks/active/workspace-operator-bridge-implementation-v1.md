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
- Remote checkpoint: 866e2805def9d7bb1e5640715a72c72efc895480
- Remote verified: true

## Next safe action

RESOLVE UT-09 REPRESENTATIVE-WORK HOTKEY COLLISION FOR CTRL+SPACE FROM VALIDATED BASE workspace-control@b84f69cf11a598d8353ef0aa1ddcb1b014026446. UT-11 IS ACCEPTED; do not rerun its 15-minute timer. The operator repeatedly pressed Ctrl+Space with Bridge OFF while Firefox was both focused and unfocused and observed no bridge reaction, focus/minimize effect, or other visible side effect. Run #494/job 133016035152 was canceled by the operator after STAGE10_USABILITY_READY and is NOT claimed as completed structured evidence. For UT-09, determine whether Ctrl+Space conflicts with any application-local shortcut the operator actually requires during representative work; preserve the frozen retention rule of zero unintended scheduler dispatches, zero required native shortcut collisions, and <=2/7 interference. Do not make the operator repeat already-observed Bridge-OFF behavior.

## Remaining work

- impl_10 final binding coverage: resolve representative-work collision UT-09 for Ctrl+Space. No further UT-11 timer run is required; Bridge-OFF behavior is accepted from direct operator observation.
- live transport gate: after Workspace Shell semantic authority exists, prove exact-host Tailscale fake-worker transport before real-account use.
- impl_12: bounded real-account calibration with no DOM/content automation, no added browser permissions and no security workaround.
- impl_09: authoritative target-machine UX-09 performance/resource benchmark after real-account calibration.
- impl_13: explicit PROMOTE_V0/HOLD/REVISE production-readiness review.

## Blockers / gates

- Ctrl+Space has accepted UT-05, UT-06, UT-07, UT-08, UT-10, UT-02, UT-03, UT-04, UT-12 and UT-11 evidence. UT-11 Bridge-OFF behavior is accepted from direct operator observation on exact validated head b84f69cf11a598d8353ef0aa1ddcb1b014026446; the canceled 15-minute harness run is explicitly not treated as completed structured evidence. The only remaining Stage-10 hotkey gate is UT-09 representative-work collision/interference.
- The authoritative long-form UX-09 target benchmark remains intentionally SUSPENDED as an intermediate gate. It remains mandatory before impl_13 production readiness can pass.
- Production action/status transport is now implemented and validated in code, but the real Tailscale Serve -> localhost backend path has not yet been activated/preflighted on the Linux Workspace Control host and Windows WorkspaceWorkers client. INST-01 remains PARTIAL until that exact-host path carries a fake-worker action end-to-end.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
