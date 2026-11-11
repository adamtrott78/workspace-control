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
- Remote checkpoint: b26dd24c6d3a7b056c75dbce5f90f6f8f735083f
- Remote verified: true

## Next safe action

DO NOT POLL OR RETRIGGER the currently active Stage-09 target run. Operator Bridge run #180 / target-performance job 130680498381 is running on exact validated head b26dd24c6d3a7b056c75dbce5f90f6f8f735083f per the operator console at handoff time. Wait for the operator to report that the job concluded or provide the completed runner output. Only then inspect the completed GitHub run/job once and interpret the authoritative result. If SUCCESS: retrieve stage09-target-evidence.json, validate its schema/provenance against exact head b26dd24c6d3a7b056c75dbce5f90f6f8f735083f, evaluate every frozen UX-09 budget, and durably promote Stage 09 only if all gates pass. If FAILURE: inspect the first fail-closed marker in priority order—STAGE09_TARGET_ADAPTER_PREFLIGHT_FAILURE, STAGE09_BACKGROUND_CPU_PREFLIGHT, STAGE09_TARGET_FIREFOX_COLLECTOR_FAILURE / TARGET_FIREFOX_PARTIAL collector failure envelope, STAGE09_FIREFOX_REPLICATE_FAILURE, scenario-specific sustained unrelated CPU rejection, or final budget failure—and repair only the demonstrated blocker. Do not weaken ADAPTER_IDENTITY_REJECTED, fake-worker-only boundaries, content-free evidence rules, process-ownership fences, exact-head binding, or frozen UX-09 thresholds. Do not begin impl_10, impl_11, impl_12, or impl_13 until Stage 09 is durably validated and promoted.

## Remaining work

- impl_09_performance_benchmark_execution: Execute UX-09 performance/resource benchmark
- impl_10_usability_trial_execution: Execute UX-11 human-in-loop simulator trials
- impl_11_webview2_comparison_spike: Conditional WebView2 custom-shell comparison
- impl_12_real_account_calibration: Bounded real-account security/policy/authentication calibration
- impl_13_production_readiness_review: Integrated implementation review and promotion decision

## Blockers / gates

- Stage 09 remains IN_PROGRESS and Stage 10+ remain blocked. Current exact implementation/handoff preparation head b26dd24c6d3a7b056c75dbce5f90f6f8f735083f passed Workspace Control Validation #2550 and Operator Bridge Validation #179. The Stage-09 target-debug sequence has corrected: Firefox first-run/default-browser contamination; signed WorkspaceWorkers profile repair; adapter-preflight diagnostics; historical Firefox/Chrome PID-lineage attribution; target baseline profile initialization; transient Process.ExitCode false failures; persistent dotnet/MSBuild/Roslyn build-server CPU leakage; total-CPU versus unrelated-CPU quiet-gate attribution; bounded CPU settling while preserving the frozen <=20 percent acceptance threshold; and Firefox completion authority so structured content-free result evidence plus clean browser state, not Windows Process.ExitCode, determines success. A persistent content-free TARGET_FIREFOX_PARTIAL collector failure envelope now records normalized_phase, normalized_error_type, normalized_message, and steady/cold result existence if the inner Firefox collector fails. Operator Bridge run #180 / target-performance job 130680498381 was launched on this exact validated head and, per the operator console at handoff time, is still running. Do not poll, retrigger, cancel, modify the benchmark, or start impl_10+ while that run is active. No Stage-09 promotion is claimed until that exact run concludes and its result is interpreted.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
