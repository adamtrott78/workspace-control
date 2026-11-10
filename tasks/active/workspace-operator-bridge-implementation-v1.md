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
- Remote checkpoint: 3fd98235678a7d6f0f728d82b4611eed8697152e
- Remote verified: true

## Next safe action

Investigate and repair the Stage-09 Firefox adapter preflight on exact head 3fd98235678a7d6f0f728d82b4611eed8697152e before another full target run. Start with operator-bridge/tools/run-stage09-target-firefox.ps1 PreflightOnly and operator-bridge/performance/Program.cs adapter-preflight. Add bounded content-free failure evidence that survives cleanup (runner.out.log, runner.err.log, fake-worker logs, preflight result if written, and Firefox launcher/remaining-process metadata only; no page/content/profile scraping). Reproduce the preflight in isolation against the already verified Stage-09-owned WorkspaceWorkers profile and Mozilla-signed 0.1.9 performance adapter. Determine whether the failing condition is adapter handshake/identity, native-host launch/binding, Firefox launcher-child lifecycle, or another mechanical preflight defect. Preserve fail-closed semantics and do not weaken ADAPTER_IDENTITY_REJECTED or adopt unrelated Firefox processes. Once isolated preflight emits TARGET_ADAPTER_PREFLIGHT PASS with adapter_version 0.1.9-perf and Firefox cleanup is clean, validate the patch on exact head, register a fresh ephemeral self-hosted runner labeled workspace-operator-target, reapply stage09-target, and execute the frozen full matrix. Do not begin impl_10+ before Stage 09 target evidence is complete.

## Remaining work

- impl_09_performance_benchmark_execution: Execute UX-09 performance/resource benchmark
- impl_10_usability_trial_execution: Execute UX-11 human-in-loop simulator trials
- impl_11_webview2_comparison_spike: Conditional WebView2 custom-shell comparison
- impl_12_real_account_calibration: Bounded real-account security/policy/authentication calibration
- impl_13_production_readiness_review: Integrated implementation review and promotion decision

## Blockers / gates

- Stage 09 target-machine acceptance is blocked at the Firefox performance-adapter identity preflight, not at runner/bootstrap setup. On exact head 3fd98235678a7d6f0f728d82b4611eed8697152e, Operator Bridge Validation run 42815030650 completed validation successfully, then target-performance job 129827357688 passed exact-head checkout, .NET setup, Python setup, interactive target-runner preconditions, and Stage09 target profile verification before failing inside Execute frozen Stage 09 target matrix. The durable log shows STAGE09_TARGET_PROFILE_VERIFIED=PASS, then Target Firefox adapter identity preflight failed; collector cleanup also warned that Firefox remained running. No stage09-target-evidence.json was produced, and the upload step reported no matching file. Do not rerun the full matrix blindly. First diagnose the PreflightOnly path in operator-bridge/tools/run-stage09-target-firefox.ps1 and the adapter-preflight handshake in operator-bridge/performance/Program.cs, persist content-free preflight stdout/stderr/result/process-lifecycle diagnostics before cleanup, and prove the dedicated WorkspaceWorkers profile connects as FIREFOX_EXTENSION / 0.1.9-perf. Only after bounded preflight PASS should a fresh ephemeral workspace-operator-target runner be registered and the full target matrix retriggered. Stage 10 remains blocked.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
