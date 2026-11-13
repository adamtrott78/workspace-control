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
- Remote checkpoint: f952a4b0dfea079469ad9d15f32efa51e9ca053b
- Remote verified: true

## Next safe action

Continue Stage 10 by implementing/executing UT-05 judgment-gate handling, UT-06/UT-07/UT-08 recovery trials, UT-12 no-work/background acknowledgment, the full Bridge-OFF UT-11 Ctrl+Space release check, and UT-09 60-minute representative-work collision testing. In parallel, define a separately authorized production OperatorBridge action/status transport to replace NoWorkOperatorActionPort/empty workload status before Stage 12 real-account calibration. Do not use a real ChatGPT account until Stage 10 and the Stage-12 predecessor gates are satisfied.

## Remaining work

- impl_10_usability_trial_execution: Execute UX-11 human-in-loop simulator trials
- impl_11_webview2_comparison_spike: Conditional WebView2 custom-shell comparison
- impl_12_real_account_calibration: Bounded real-account security/policy/authentication calibration
- impl_09_performance_benchmark_execution: Deferred authoritative UX-09 performance/resource benchmark before production readiness
- impl_13_production_readiness_review: Integrated implementation review and promotion decision

## Blockers / gates

- Ctrl+Space passed UT-10 motor rhythm, UT-02 mixed-batch/minimize-on-empty, UT-03 interruption recovery, and UT-04 multiple SENT/UNCONFIRMED coexistence. Final binding retention still requires UT-05 through UT-08, UT-12, Bridge-OFF UT-11, and UT-09 representative-work collision testing.
- The production helper still uses NoWorkOperatorActionPort and an empty workload-status provider. An explicitly authorized production OperatorBridge action/status transport is required before real-account Stage 12 can service actual scheduler work.
- The authoritative long-form UX-09 target benchmark remains intentionally SUSPENDED as an intermediate gate. It remains mandatory before impl_13 production readiness can pass.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
