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
- Remote checkpoint: e244efad098df6559dae5874b5783782a305cf32
- Remote verified: true

## Next safe action

After this task/handoff checkpoint itself passes both hosted validators, prepare one fresh authoritative Stage-09 target attempt from the resulting exact durable PR head. Before triggering, confirm the interactive Windows runner labeled workspace-operator-target is listening, close pre-existing Firefox/Chrome/WorkspaceOperator processes, keep the workstation on AC power, keep Chrome Memory Saver disabled, and avoid sustained CPU-heavy work. Trigger stage09-target exactly once, then FREEZE THE PR BRANCH until target-performance reaches a terminal state. If it fails, inspect STAGE09_FIREFOX_REPLICATE_COLLECTOR_FAILURE and STAGE09_FIREFOX_REPLICATE_INCOMPLETE first; the new fail-fast boundary should expose the inner Firefox blocker immediately instead of allowing hours of later measurements. If it succeeds, retrieve and validate stage09-target-evidence.json and promote Stage 09 only if every frozen UX-09 budget passes. Do not begin impl_10, impl_11, impl_12, or impl_13 until Stage 09 is durably validated and promoted.

## Remaining work

- impl_09_performance_benchmark_execution: Execute UX-09 performance/resource benchmark
- impl_10_usability_trial_execution: Execute UX-11 human-in-loop simulator trials
- impl_11_webview2_comparison_spike: Conditional WebView2 custom-shell comparison
- impl_12_real_account_calibration: Bounded real-account security/policy/authentication calibration
- impl_13_production_readiness_review: Integrated implementation review and promotion decision

## Blockers / gates

- Stage 09 remains IN_PROGRESS and Stage 10+ remain blocked. Operator Bridge run #185 / target-performance job 130715185761 on source head 819011a0e52dc6816eb5bf918e8ff63fd10fd936 is INVALID FOR ACCEPTANCE: it failed before stage09-target-evidence.json was produced. The job passed target profile verification, adapter preflight, and the early unrelated-CPU validity gate, then completed deep target resource measurement before failing with 'Full Firefox replicate is missing exact latency evidence.' The exact inner Firefox collector cause is not recoverable from #185 because child stdout/stderr were redirected and replicate temporaries were cleaned up; therefore do not claim a specific COLLECTOR_FAILURE root cause. The demonstrated harness defect was that incomplete or collector-failure TARGET_FIREFOX_PARTIAL evidence could pass the replicate boundary and fail only at final aggregation. Exact repair head e244efad098df6559dae5874b5783782a305cf32 fixes that propagation/shape gate and passed Workspace Control #2557 plus Operator Bridge #186. A fresh target run is required to expose the underlying inner Firefox blocker or produce valid complete target evidence.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
