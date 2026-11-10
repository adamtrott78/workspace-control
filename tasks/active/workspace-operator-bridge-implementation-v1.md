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

Wait only for Mozilla AMO to finish signing the accepted unlisted/self-distributed Stage-09 Firefox performance adapter submission built from validated implementation source head 96be6cf95706f784f7f20c3a5a61a7671b36fa27. When the signed XPI is available, verify its payload against the exact Stage-09 source using operator-bridge/performance/prepare-stage09-target-profile.ps1, run that script once with -InteractiveInstall to create/use only the Stage-09-owned WorkspaceWorkers profile and complete Firefox's normal add-on confirmation, close Firefox, then re-register the Windows workstation as an interactive ephemeral GitHub self-hosted runner with label workspace-operator-target and trigger the hardened Stage-09 target job. Do not begin impl_10+ before Stage 09 target evidence is validated.

## Remaining work

- impl_09_performance_benchmark_execution: Execute UX-09 performance/resource benchmark
- impl_10_usability_trial_execution: Execute UX-11 human-in-loop simulator trials
- impl_11_webview2_comparison_spike: Conditional WebView2 custom-shell comparison
- impl_12_real_account_calibration: Bounded real-account security/policy/authentication calibration
- impl_13_production_readiness_review: Integrated implementation review and promotion decision

## Blockers / gates

- Stage 09 target-machine acceptance is externally blocked on Mozilla AMO signature completion for the accepted unlisted/self-distributed Firefox performance adapter. The corrected source head 96be6cf95706f784f7f20c3a5a61a7671b36fa27 passed Workspace Control Validation run 42806204793 and Operator Bridge Validation run 42806204561. AMO accepted the add-on and reviewer source bundle and now reports Version Signature Pending. No target performance result exists yet. After signing, install only into the Stage-09-owned WorkspaceWorkers profile, run adapter identity preflight, then re-register the ephemeral interactive Windows runner and execute the target matrix. Stage 10 remains blocked.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
