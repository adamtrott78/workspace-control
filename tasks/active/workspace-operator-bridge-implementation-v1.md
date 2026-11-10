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
- Remote checkpoint: 8c0f97f23e181b850728b2b42c970b71d93c3991
- Remote verified: true

## Next safe action

Execute impl_07_recovery_and_fault_closure from architecture/workspace-semantic-execution-operator-implementation-stage-plan.v0.1.json. Implement the recovery coordinator, restart/reinventory handling, auth-domain freeze/reconcile/generation-advance flow, and content-free recovery traces using the validated real helper/browser adapters plus deterministic fault injection. Required exit evidence: every frozen UX-10 recovery/crash/generation fixture at its required implemented layer passes; each recovery_id advances generation at most once; late old-generation evidence cannot advance current state; cold restart never replays stale local cache; and Ctrl+B during blocking recovery cannot stage a worker packet or mutate the clipboard. Preserve all UX-07/UX-08 authority and privacy boundaries. Do not widen into packaging, UX-09 performance acceptance, UX-11 usability trials, WebView2 promotion, or real-account calibration.

## Remaining work

- impl_07_recovery_and_fault_closure: Crash, auth-domain, stale-generation, restart, and recovery closure
- impl_08_packaging_install_update_rollback: Per-user packaging, signed-extension flow, install/uninstall, and rollback
- impl_09_performance_benchmark_execution: Execute UX-09 performance/resource benchmark
- impl_10_usability_trial_execution: Execute UX-11 human-in-loop simulator trials
- impl_11_webview2_comparison_spike: Conditional WebView2 custom-shell comparison
- impl_12_real_account_calibration: Bounded real-account security/policy/authentication calibration
- impl_13_production_readiness_review: Integrated implementation review and promotion decision

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
