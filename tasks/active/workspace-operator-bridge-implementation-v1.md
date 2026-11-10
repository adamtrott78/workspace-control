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
- Remote checkpoint: 832777a8015d6ef9ee2bdedf22553e28a6549553
- Remote verified: true

## Next safe action

Explicitly register/connect the actual Windows operator workstation as an interactive GitHub self-hosted Windows x64 runner with additional label workspace-operator-target. Then workflow-dispatch .github/workflows/operator-bridge-validation.yml at exact checkpoint 832777a8015d6ef9ee2bdedf22553e28a6549553 with run_target_benchmark=true, confirm_ac_power=true, and confirm_chrome_memory_saver_disabled=true. After the target-performance job finishes, retrieve operator-bridge-stage09-target-832777a8015d6ef9ee2bdedf22553e28a6549553, evaluate stage09-target-evidence.json, correct or explicitly escalate any failing frozen budget, and only then promote Stage 09. Do not begin impl_10, impl_11, impl_12, or impl_13 before Stage 09 is durably validated.

## Remaining work

- impl_09_performance_benchmark_execution: Execute UX-09 performance/resource benchmark
- impl_10_usability_trial_execution: Execute UX-11 human-in-loop simulator trials
- impl_11_webview2_comparison_spike: Conditional WebView2 custom-shell comparison
- impl_12_real_account_calibration: Bounded real-account security/policy/authentication calibration
- impl_13_production_readiness_review: Integrated implementation review and promotion decision

## Blockers / gates

- Stage 09 target-machine acceptance is blocked only on explicit connection of the real Windows operator workstation to the already-validated GitHub target path. The workstation must be registered as a self-hosted Windows x64 runner with additional label workspace-operator-target and started interactively under the Windows user that owns the WorkspaceWorkers Firefox profile and Stage-08 HKCU Native Messaging registration. After registration, dispatch Operator Bridge Validation on exact Stage-09 checkpoint 832777a8015d6ef9ee2bdedf22553e28a6549553 with run_target_benchmark=true, confirm_ac_power=true, and confirm_chrome_memory_saver_disabled=true. The target job will run exact-head validation first, execute the frozen full matrix, and upload stage09-target-evidence.json. Stage 10 remains blocked until that evidence is evaluated and every failing mechanical budget is corrected or explicitly escalated.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
