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

Prepare one fresh authoritative Stage-09 target attempt from the current fully validated durable head, then FREEZE THE PR BRANCH until that target run concludes: do not commit task/handoff/code/docs, do not trigger another Operator Bridge workflow, and do not otherwise create a competing run in the PR-scoped concurrency group while target-performance is active. Before triggering, keep the interactive Windows runner labeled workspace-operator-target listening, close pre-existing Firefox/Chrome/WorkspaceOperator processes, and use the existing bounded CPU-settle path without weakening the frozen <=20% unrelated-CPU rule. After triggering stage09-target, make no branch mutations until the operator reports completion. If the target job succeeds, retrieve stage09-target-evidence.json, validate schema/provenance against the exact run source SHA, evaluate every frozen UX-09 budget, and promote Stage 09 only if all checks pass. If it fails, inspect the first fail-closed marker and repair only the demonstrated blocker. If it is cancelled again, first inspect workflow concurrency/event history before attributing it to the workstation or operator. Do not begin impl_10, impl_11, impl_12, or impl_13 until Stage 09 is durably validated and promoted.

## Remaining work

- impl_09_performance_benchmark_execution: Execute UX-09 performance/resource benchmark
- impl_10_usability_trial_execution: Execute UX-11 human-in-loop simulator trials
- impl_11_webview2_comparison_spike: Conditional WebView2 custom-shell comparison
- impl_12_real_account_calibration: Bounded real-account security/policy/authentication calibration
- impl_13_production_readiness_review: Integrated implementation review and promotion decision

## Blockers / gates

- Stage 09 remains IN_PROGRESS and Stage 10+ remain blocked. Operator Bridge run #180 / target-performance job 130680498381 on source head b26dd24c6d3a7b056c75dbce5f90f6f8f735083f is classified as INTERRUPTED/CANCELLED, not a benchmark failure and not a UX-09 verdict. The run passed hosted validation, STAGE09_TARGET_PROFILE_VERIFIED=PASS, STAGE09_TARGET_ADAPTER_PREFLIGHT=PASS, and the bounded unrelated-CPU gate on attempt 2 with mean 17.1189% <= 20%. It then progressed through the Firefox resource path and deep into Chrome resource measurement before cancellation; the last bounded browser evidence showed only historically owned Chrome processes. At cancellation, Windows PowerShell was interrupted while executing Stop-TrackedProcessName at run-stage09-target-matrix.ps1 line 326 and GitHub reported 'The operation was canceled.' No stage09-target-evidence.json was produced, so partial measurements are not admissible for Stage-09 acceptance. Root cause of cancellation is repository-workflow concurrency: .github/workflows/operator-bridge-validation.yml uses PR-scoped group operator-bridge-validation-${{ github.event.pull_request.number || github.ref }} with cancel-in-progress: true, and the task/handoff paths are pull_request trigger paths. Prior-executor handoff commit 25f598d094309cd99550d0eb2be7fdd368fe5abe triggered run #181 at 17:55:47Z, then handoff-sync commit 06c37ac44d4dd5616d1bf3c7a554e9750f87c9c9 triggered run #182 at 17:55:58Z; #181 was immediately cancelled and active target run #180 was then cancelled by the same concurrency group. Therefore the cancellation was caused by branch mutations during the active target run, not by the operator's local interaction.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
