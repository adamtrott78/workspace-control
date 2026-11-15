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
- Remote checkpoint: 931882bce5a34c597888e2eaa1a40650d5b31c58
- Remote verified: true

## Next safe action

FIX AND RE-ACCEPT UT-12 FROM VALIDATED IMPLEMENTATION BASE workspace-control@931882bce5a34c597888e2eaa1a40650d5b31c58. DO NOT REDO UT-05–UT-08: those human trials are accepted. UT-12 run #485/job 133000812535 emitted structured OBJECTIVE_PASS, but operator-visible acceptance failed because READY=0 Ctrl+Space minimizes WorkspaceWorkers Firefox only when Firefox is already foreground; if another app/window is foreground, it does not minimize. Current code re-captures only foreground Firefox at the UT-12 NoAction press and MinimizeCapturedWorkerWindow refuses unless the captured HWND is also GetForegroundWindow(). Make the smallest bounded correction: preserve/resolve the already trusted dedicated WorkspaceWorkers Firefox HWND before the no-work press and allow minimizing that trusted captured HWND while another app is foreground, without bringing Firefox forward; fail closed on stale/ambiguous/non-Firefox HWND and never minimize arbitrary Firefox. Validate the exact head, then rerun UT-12 with (1) Firefox foreground and (2) Firefox background after clicking another app on the second monitor; require minimize success in both cases and preserve the already-passing background durable-ack invariants: zero focus steal, zero clipboard write, zero browser service effect. Only after UT-12 passes, run Bridge-OFF UT-11 and representative-work collision UT-09.

## Remaining work

- impl_10 UT-12: correct the focus-dependent READY=0 minimize path so the already trusted dedicated WorkspaceWorkers Firefox HWND can be minimized while another app is foreground; preserve fail-closed identity and no focus steal.
- impl_10 UT-12 acceptance: rerun with Firefox foreground and background/other-app focus; require minimize success in both plus background durable ack with zero clipboard/browser/focus disruption.
- impl_10 final binding coverage: execute Bridge-OFF UT-11 and representative-work collision UT-09; preserve no-response/no-wrong-window guarantees.
- live transport gate: after Workspace Shell semantic authority exists, prove exact-host Tailscale fake-worker transport before real-account use.
- impl_12: bounded real-account calibration with no DOM/content automation, no added browser permissions and no security workaround.
- impl_09: authoritative target-machine UX-09 performance/resource benchmark after real-account calibration.
- impl_13: explicit PROMOTE_V0/HOLD/REVISE production-readiness review.

## Blockers / gates

- Ctrl+Space has accepted UT-05, UT-06, UT-07, UT-08, UT-10, UT-02, UT-03 and UT-04 evidence. Final retention is blocked by UT-12 focus-independent READY=0 minimization: current run #485 minimizes only while Firefox is foreground. After that correction/acceptance, Bridge-OFF UT-11 and representative-work collision UT-09 remain required.
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
