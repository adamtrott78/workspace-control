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
- Remote checkpoint: 544911b724aa0c943786a285a6e38213a861667e
- Remote verified: false

## Next safe action

Start or keep an interactive Windows self-hosted runner labeled workspace-operator-target listening so queued target-preflight job 129899072941 can execute on exact head 544911b724aa0c943786a285a6e38213a861667e. The profile verifier will emit only bounded content-free add-on runtime state (extension id/version/active/userDisabled/appDisabled/signedState) before launch. If the expected 0.1.9 adapter is inactive/disabled, repair the dedicated Stage-09 WorkspaceWorkers signed-add-on install state without touching unrelated Firefox/profile data, then re-run isolated preflight. If it is active/enabled yet ADAPTER_CONNECTION_NOT_OBSERVED persists, investigate Firefox MV3 background/event-page startup/wake and graceful owned-process shutdown semantics using the existing fake-worker-only profile; preserve ADAPTER_IDENTITY_REJECTED, exact-head native-host binding, process ownership, and content-free evidence. Only after isolated preflight again emits TARGET_ADAPTER_PREFLIGHT PASS with adapter_version 0.1.9-perf on the repaired exact head, run both hosted validators to SUCCESS and then trigger a fresh full frozen Stage-09 target matrix. Do not begin impl_10+.

## Remaining work

- impl_09_performance_benchmark_execution: Execute UX-09 performance/resource benchmark
- impl_10_usability_trial_execution: Execute UX-11 human-in-loop simulator trials
- impl_11_webview2_comparison_spike: Conditional WebView2 custom-shell comparison
- impl_12_real_account_calibration: Bounded real-account security/policy/authentication calibration
- impl_13_production_readiness_review: Integrated implementation review and promotion decision

## Blockers / gates

- Stage 09 remains IN_PROGRESS. Exact head 8d50ef0b87b85480d10452d88965a0a616e2c2af passed Workspace Control Validation #2474, Operator Bridge Validation #105, and isolated target-preflight job 129889811928 / run 42833594686 with TARGET_ADAPTER_PREFLIGHT PASS, adapter_kind FIREFOX_EXTENSION, adapter_version 0.1.9-perf. A subsequent full target attempt, Operator Bridge run 42834251364 / target-performance job 129894144174, again failed before any UX-09 measurement because the same preflight emitted failing/invalid evidence. No stage09-target-evidence.json was produced. Immediately afterward, isolated preflight job 129896159398 / run 42835407614 reproduced the failure. Artifact 13773931227 shows normalized_failure ADAPTER_CONNECTION_NOT_OBSERVED, only native_helper bridge_toggle ENABLED in diagnostics, launcher_has_exited=true, runner_exit_code=0, remaining_firefox_process_count=0: Firefox launched and cleaned up, helper was ready, but the signed extension never connected. This proves the regression is persistent Firefox/profile add-on runtime state or startup/wake behavior, not adapter identity rejection, native-host identity mismatch, or leaked Firefox processes. Current diagnostic head 544911b724aa0c943786a285a6e38213a861667e adds content-free Firefox extensions.json runtime verification for the expected signed adapter. Target-preflight job 129899072941 is queued and currently blocked only on an interactive self-hosted runner labeled workspace-operator-target. Do not rerun the full matrix until this diagnostic identifies whether the installed adapter is still active/enabled.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
