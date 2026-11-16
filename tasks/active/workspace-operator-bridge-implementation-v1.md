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

RUN AND ACCEPT BRIDGE-OFF UT-11 FROM VALIDATED IMPLEMENTATION BASE workspace-control@866e2805def9d7bb1e5640715a72c72efc895480. UT-12 IS ACCEPTED AND MUST NOT BE REDONE: foreground case #489 and off-foreground case #492 both produced OBJECTIVE_PASS with successful trusted-window minimize, delayed durable acknowledgment, zero clipboard/browser/focus side effects, and operator-visible confirmation. For UT-11, prove the bridge OFF state does not service Ctrl+Space, does not write clipboard, and does not focus/minimize or otherwise affect any browser/window. After UT-11 passes, execute representative-work collision UT-09. Preserve Ctrl+Space -> Ctrl+V -> Enter for normal service, pending-action refocus/block semantics, and READY=0 minimize of only the already trusted WorkspaceWorkers Firefox HWND.

## Remaining work

- impl_10 remaining human coverage: execute and accept Bridge-OFF UT-11, then representative-work collision UT-09; preserve no-response/no-wrong-window guarantees and the accepted Ctrl+Space behavior.
- live transport gate: after Workspace Shell semantic authority exists, prove exact-host Tailscale fake-worker transport before real-account use.
- impl_12: bounded real-account calibration with no DOM/content automation, no added browser permissions and no security workaround.
- impl_09: authoritative target-machine UX-09 performance/resource benchmark after real-account calibration.
- impl_13: explicit PROMOTE_V0/HOLD/REVISE production-readiness review.

## Blockers / gates

- Ctrl+Space has accepted UT-05, UT-06, UT-07, UT-08, UT-10, UT-02, UT-03, UT-04 and UT-12 evidence. UT-12 focus-independent READY=0 minimization is accepted on exact corrected head 866e2805def9d7bb1e5640715a72c72efc895480; remaining Stage-10 human coverage is Bridge-OFF UT-11 followed by representative-work collision UT-09.
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
