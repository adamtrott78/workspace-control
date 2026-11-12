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
- Remote checkpoint: 62e9260f2451d51cdc8b2d724cabbe5691e39ef9
- Remote verified: true

## Next safe action

Validate the runtime-configurable Ctrl+Space candidate at exact head. After Workspace Control and Operator Bridge validation pass, rerun implemented Stage-10 trials in this order on the interactive foreground Windows runner: UT-11 to prove Bridge OFF releases Ctrl+Space, UT-01 to reconfirm the 5-action/repeated-hotkey recovery path using Ctrl+Space, then UT-10 for 20 normal Ctrl+Space -> Ctrl+V -> Enter cycles. During these trials, ask the operator to judge whether Ctrl+Space actually resolves the finger-stretch complaint; do not treat the candidate as operator-accepted until observed. Capture routine rhythm friction and worker-selection confidence after UT-10. Do not retain Ctrl+Space as final until UT-09 representative-work collision testing passes. Keep Stage 09 target benchmarking deferred.

## Remaining work

- impl_10_usability_trial_execution: Execute UX-11 human-in-loop simulator trials
- impl_11_webview2_comparison_spike: Conditional WebView2 custom-shell comparison
- impl_12_real_account_calibration: Bounded real-account security/policy/authentication calibration
- impl_09_performance_benchmark_execution: Deferred authoritative UX-09 performance/resource benchmark before production readiness
- impl_13_production_readiness_review: Integrated implementation review and promotion decision

## Blockers / gates

- Ctrl+Space is the selected Stage-10 candidate binding but is not yet empirically accepted. Exact-head validation must pass, then rerun UT-11, UT-01, and UT-10 on Ctrl+Space; later hotkey-sensitive UT-02, UT-03, and UT-09 must also pass before final retention.
- The authoritative long-form UX-09 target benchmark remains intentionally SUSPENDED as an intermediate gate. Do not rerun it during Stage-10 work. It remains mandatory before impl_13 production readiness can pass.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
