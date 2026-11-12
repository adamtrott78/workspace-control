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
- Remote checkpoint: 62e9260f2451d51cdc8b2d724cabbe5691e39ef9
- Remote verified: true

## Next safe action

Continue impl_10 on validated implementation head 62e9260f2451d51cdc8b2d724cabbe5691e39ef9. Ensure the interactive Windows runner workspace-operator-target is listening in the logged-in desktop session. If needed, from PowerShell: Set-Location C:\Users\ATrott\actions-runner; verify no active Runner.Worker job; if the foreground runner is absent run .\run.cmd. Do NOT run Stage-10 as a Windows service/session-0 runner because the trial requires [Environment]::UserInteractive and real foreground browser/hotkey behavior. Prefer rerunning only failed Stage-10 job 130957988034 rather than cycling the PR label and replaying hosted validation. For the first action deliberately test Ctrl+B -> Ctrl+V -> Ctrl+B, do not Enter yet; second Ctrl+B must refocus/retain the same AwaitingDurableAck worker/action and must not advance the queue. Then Enter, confirm durable acknowledgment, finish the remaining UT-01 actions, inspect structured result, and continue remaining Stage-10 usability trials. Keep Stage 09 deferred until final production gating.

## Remaining work

- impl_10_usability_trial_execution: Execute UX-11 human-in-loop simulator trials
- impl_11_webview2_comparison_spike: Conditional WebView2 custom-shell comparison
- impl_12_real_account_calibration: Bounded real-account security/policy/authentication calibration
- impl_09_performance_benchmark_execution: Deferred authoritative UX-09 performance/resource benchmark before production readiness
- impl_13_production_readiness_review: Integrated implementation review and promotion decision

## Blockers / gates

- Stage 10 recovery validation remains open: human-test the AwaitingDurableAck same-worker refocus on exact validated implementation head 62e9260f2451d51cdc8b2d724cabbe5691e39ef9. Exact sequence: Ctrl+B -> Ctrl+V -> Ctrl+B again, do not press Enter yet; verify the second Ctrl+B keeps/refocuses the same worker and does not advance to the next action, then press Enter to durably acknowledge and continue the trial.
- The authoritative long-form UX-09 target benchmark remains intentionally SUSPENDED as an intermediate gate. Do not rerun it during Stage-10 work. It remains mandatory before impl_13 production readiness can pass.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
