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
- Remote checkpoint: 0a110b570410d6d3310afc8ef4591e4aa383c0b8
- Remote verified: true

## Next safe action

Validate the child task/program creation at the exact repository head. If Workspace Control Validation passes, mark impl_00_program_authority_and_contract_freeze VALIDATED, refresh restore-point:latest to that validated head, and begin impl_01_repository_bootstrap_and_contract_harness. Do not create implementation code before the Stage 00 authority/program checkpoint is validated.

## Remaining work

- impl_01_repository_bootstrap_and_contract_harness: Repository skeleton, build, CI, and frozen-contract harness
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
