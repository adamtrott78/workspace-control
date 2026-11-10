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
- Remote checkpoint: c2e06d8b5efdffc3e35f17879651d0f058281463
- Remote verified: true

## Next safe action

Run the validated Stage-09 target-workstation benchmark from checkpoint c2e06d8b5efdffc3e35f17879651d0f058281463 on an authorized connected Windows operator workstation. Use operator-bridge/performance/TARGET-RUN.md, operator-bridge/performance/stage09-target-evidence.schema.json, and operator-bridge/tools/run-stage09-target-firefox.ps1 as bounded inputs; complete the mandatory Firefox/Chrome three-replicate parity matrix, Chrome Memory Saver control, five discard/restore replicates, exact latency repetition counts including 10 cold starts, and aggregate frozen-budget evaluation. Do not begin impl_10 UX-11 usability trials, impl_11 WebView2 comparison/promotion, impl_12 real-account calibration, or impl_13 readiness review until Stage 09 is durably validated.

## Remaining work

- impl_09_performance_benchmark_execution: Execute UX-09 performance/resource benchmark
- impl_10_usability_trial_execution: Execute UX-11 human-in-loop simulator trials
- impl_11_webview2_comparison_spike: Conditional WebView2 custom-shell comparison
- impl_12_real_account_calibration: Bounded real-account security/policy/authentication calibration
- impl_13_production_readiness_review: Integrated implementation review and promotion decision

## Blockers / gates

- Stage 09 target-machine acceptance is blocked because no authorized connected target Windows operator workstation or self-hosted target runner is available to this executor. GitHub windows-latest is explicitly non-target evidence. Before Stage 10, execute the frozen UX-09 target matrix on the real operator workstation: 60s warm-up + 120s 1Hz steady-state windows, three Firefox/Chrome resource replicates with order alternation, Chrome Memory Saver disabled/recorded, five discard/restore replicates, and latency counts reuse=50, restore=30, create=30, cold-start=10, local-primitives=100; then evaluate every frozen budget and correct or explicitly escalate any failure.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
