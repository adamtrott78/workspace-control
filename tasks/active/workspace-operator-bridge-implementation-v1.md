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
- Remote checkpoint: 0891a0fde2da7f763a0589c03ef3daf63ef5b3c7
- Remote verified: true

## Next safe action

Keep the interactive Windows self-hosted runner labeled workspace-operator-target available. Normal work, including Chrome use, is allowed while Stage 09 is not actively running. For the next authoritative full Stage-09 target attempt, first enter a short controlled benchmark window: close all pre-existing Firefox, Chrome, and WorkspaceOperator processes and avoid sustained CPU-heavy foreground/background work. Trigger the stage09-target path on exact validated head 0891a0fde2da7f763a0589c03ef3daf63ef5b3c7. The new 10-second STAGE09_BACKGROUND_CPU_PREFLIGHT must pass mean total CPU <= 20 percent before the expensive matrix proceeds; if it fails, do not rerun blindly—identify the local load and retry only when quiet. If the gate passes, let the frozen Firefox/Chrome matrix run without interacting with benchmark-owned browser windows. Do not begin impl_10+ until stage09-target-evidence.json is produced, validates, and every frozen UX-09 budget passes.

## Remaining work

- impl_09_performance_benchmark_execution: Execute UX-09 performance/resource benchmark
- impl_10_usability_trial_execution: Execute UX-11 human-in-loop simulator trials
- impl_11_webview2_comparison_spike: Conditional WebView2 custom-shell comparison
- impl_12_real_account_calibration: Bounded real-account security/policy/authentication calibration
- impl_13_production_readiness_review: Integrated implementation review and promotion decision

## Blockers / gates

- Stage 09 remains IN_PROGRESS and Stage 10+ remain blocked. The implementation/debug sequence has eliminated the prior Firefox profile/runtime and process-attribution defects: signed adapter preflight passes, historical Firefox PID lineage is tracked, null Start-Process ExitCode races are finalized before evaluation, and content-free lifecycle/child-failure diagnostics are present. Full target run Operator Bridge #151 / target-performance job 130585620068 on exact head c938676f999fa015d5dbc7efd2fab588d1012fd4 progressed into the real frozen matrix and then failed closed only because sustained unrelated CPU exceeded the frozen 20 percent validity ceiling. No stage09-target-evidence.json was produced. Current exact head 0891a0fde2da7f763a0589c03ef3daf63ef5b3c7 adds a 10-second early background-CPU preflight plus scenario-specific unrelated-CPU diagnostics without weakening the 20 percent acceptance threshold. Workspace Control Validation #2520 and Operator Bridge Validation #153 are SUCCESS on that exact head. Remaining blocker is an environmental quiet-workstation window for the authoritative full target matrix, not an unresolved code defect.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
