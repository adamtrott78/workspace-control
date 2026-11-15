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
- Remote checkpoint: b5695e8c42c546d549742279a54e5668874fdacc
- Remote verified: true

## Next safe action

Continue remaining Stage-10 usability gates (UT-05 through UT-08, UT-12, Bridge-OFF UT-11, and UT-09 representative-work collision testing) while the backend completes durable packet-source materialization and server composition. Then run a separately reviewed exact-host Tailscale transport preflight using a fake worker before Stage-12 real-account calibration. Do not enable a real ChatGPT account or widen browser permissions before those predecessor gates pass.

## Remaining work

- impl_10_usability_trial_execution: Execute UX-11 human-in-loop simulator trials
- impl_11_webview2_comparison_spike: Conditional WebView2 custom-shell comparison
- impl_12_real_account_calibration: Bounded real-account security/policy/authentication calibration
- impl_09_performance_benchmark_execution: Deferred authoritative UX-09 performance/resource benchmark before production readiness
- impl_13_production_readiness_review: Integrated implementation review and promotion decision

## Blockers / gates

- Ctrl+Space passed UT-10 motor rhythm, UT-02 mixed-batch/minimize-on-empty, UT-03 interruption recovery, and UT-04 multiple SENT/UNCONFIRMED coexistence. Final binding retention still requires UT-05 through UT-08, UT-12, Bridge-OFF UT-11, and UT-09 representative-work collision testing.
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
