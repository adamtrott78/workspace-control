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

Wait only for Mozilla AMO to finish signing the accepted unlisted/self-distributed Stage-09 Firefox performance adapter submission built from validated implementation source head `96be6cf95706f784f7f20c3a5a61a7671b36fa27`.

When the signed XPI is available:

1. Verify its payload against the exact Stage-09 source with `operator-bridge/performance/prepare-stage09-target-profile.ps1`.
2. Run the prep script once with `-InteractiveInstall` to create/use only the Stage-09-owned `WorkspaceWorkers` profile and complete Firefox's normal signed-add-on confirmation.
3. Close Firefox.
4. Re-register the Windows workstation as an interactive **ephemeral** GitHub self-hosted runner with label `workspace-operator-target`.
5. Trigger the hardened Stage-09 target job, retrieve `stage09-target-evidence.json`, and evaluate every frozen UX-09 budget.

Do not begin impl_10, impl_11, impl_12, or impl_13 before Stage 09 target evidence is durably validated.

## Remaining work

- impl_09_performance_benchmark_execution: Execute UX-09 performance/resource benchmark
- impl_10_usability_trial_execution: Execute UX-11 human-in-loop simulator trials
- impl_11_webview2_comparison_spike: Conditional WebView2 custom-shell comparison
- impl_12_real_account_calibration: Bounded real-account security/policy/authentication calibration
- impl_13_production_readiness_review: Integrated implementation review and promotion decision

## Blockers / gates

Stage 09 is externally blocked only on Mozilla AMO signature completion. The corrected AMO-compatible source head `96be6cf95706f784f7f20c3a5a61a7671b36fa27` passed:

- Workspace Control Validation run `42806204793` — SUCCESS
- Operator Bridge Validation run `42806204561` — SUCCESS

AMO accepted the unlisted/self-distributed add-on plus reviewer source package and currently reports **Version Signature Pending**. No target performance result exists yet.

The target path is hardened before rerun: adapter identity is fenced to `FIREFOX_EXTENSION / 0.1.9-perf`, the signed XPI payload is verified against repo source, production `chatgpt.com` worker URLs are rejected from the benchmark package, Stage-09 profile ownership is enforced, Native Messaging override cleanup is reversible, and Chrome Memory Saver is disabled through a reversible per-user policy during measurement.

After the signature is available, complete the signed-add-on install into the Stage-09-owned `WorkspaceWorkers` profile, run adapter preflight, re-register the ephemeral interactive Windows runner, and execute Stage 09. Stage 10 remains blocked until every required target budget is evaluated.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
