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
- Remote checkpoint: 0fabe069aa39914f84b00ac78a2f26f57238ef4c
- Remote verified: true

## Next safe action

Execute impl_02_windows_helper_kernel from architecture/workspace-semantic-execution-operator-implementation-stage-plan.v0.1.json. Implement the primary .NET helper kernel only: tray/master ON-OFF state, Win32 RegisterHotKey adapter, STA write-only clipboard adapter, single-flight dispatch coordinator, content-free structured diagnostics, monotonic timing, and fake application/BrowserPort boundaries. Do not implement Native Messaging, named pipes, Firefox lifecycle, simulator worker behavior, or real-account interaction in Stage 02. Required exit evidence includes hotkey register/unregister/conflict behavior, bridge-OFF no-side-effect behavior, held-repeat/single-flight suppression, last-safe-moment clipboard tests using fake BrowserPort, logging denylist tests, and a recorded helper idle-resource measurement.

## Remaining work

- impl_02_windows_helper_kernel: Windows helper kernel
- impl_03_native_messaging_and_local_ipc: Native Messaging proxy and same-user local IPC
- impl_04_firefox_mv3_adapter: Firefox Manifest V3 browser adapter
- impl_05_simulator_and_fake_worker: Deterministic simulator and local fake worker
- impl_06_integrated_local_bridge_e2e: Real helper + Firefox + fake-worker integration
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
