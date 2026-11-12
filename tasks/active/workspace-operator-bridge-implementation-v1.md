<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-operator-bridge-implementation-v1
- Title: Workspace Operator Bridge Implementation v1
- Status: IN_PROGRESS
- Parent: workspace-semantic-execution-migration-v1
- Branch: workspace-semantic-execution-migration-v1
- PR: #590
- Current stage: impl_10_usability_trial_execution

## Current validated implementation checkpoint

- Implementation head: `62e9260f2451d51cdc8b2d724cabbe5691e39ef9`
- Workspace Control Validation #2572: SUCCESS
- Operator Bridge Validation #209: SUCCESS
- Stage 09 target benchmark: DEFERRED/SUSPENDED as an intermediate gate; still mandatory before Stage 13 production readiness.

## Stage-10 evidence

- UT-11: PASS on run #194 / job `130809245969`.
- UT-01 primary operator loop is functional.
- Clean happy-path UT-01: run #208 / job `130950231898` on `b5d9ae62...` completed 5/5 actions, 5/5 durable acknowledgments, OBJECTIVE_PASS.
- Recovery rerun job `130952654587`: 13 hotkey presses, 8 repeat presses blocked, 5/5 actions completed, 5/5 durable acks, but 2 rejected submissions. Operator observed:
  - repeat Ctrl+B before paste was blocked;
  - after paste but before Enter, Ctrl+B could still move tabs.
- Paste alone is NOT acknowledgment. Only Enter/fake-worker submit can durably acknowledge the prepared action.
- Current repair `62e9260f...`: while any simulator action is `AwaitingDurableAck`, repeated Ctrl+B must not claim the next action; it must idempotently refocus/retain that same worker binding until Enter/durable ack.
- Follow-up run #210 / job `130957988034` on `62e9260f...` reached `STAGE10_USABILITY_READY=UT-01`, then hit the 30-minute wrapper timeout with no result artifact because the final human recovery sequence was not completed. Treat as NO VERDICT, not product failure.

## Exact next action

1. Ensure the interactive Windows self-hosted runner labeled `workspace-operator-target` is listening in the logged-in desktop session.
2. Prefer GitHub **rerun only job `130957988034`**. Do not cycle the Stage-10 label unless necessary; that needlessly replays hosted validation.
3. Close pre-existing Firefox and WorkspaceOperator before the job starts.
4. When UT-01 is READY, deliberately test the unresolved case:
   - `Ctrl+B`
   - `Ctrl+V`
   - `Ctrl+B` again
   - **do not press Enter yet**
5. Expected: second Ctrl+B does not advance to another action; it keeps/refocuses the same worker/action and preserves the pending handoff.
6. Then press Enter to create the durable acknowledgment.
7. Continue the remaining UT-01 actions and inspect the structured result.
8. If the recovery case passes, continue the remaining required Stage-10 usability trials. Do not restart the long Stage-09 target matrix during routine Stage-10 work.

## Windows runner restart

Stage-10 requires an **interactive foreground runner**, not a Windows service/session-0 runner.

PowerShell, when no GitHub job is active:

```powershell
Set-Location C:\Users\ATrott\actions-runner

# See whether a runner listener/worker is already alive.
Get-Process -Name Runner.Listener,Runner.Worker -ErrorAction SilentlyContinue

# If a stale listener/worker must be force-restarted, only do this when no job is active:
Get-Process -Name Runner.Listener,Runner.Worker -ErrorAction SilentlyContinue |
    Stop-Process -Force

# Start the persistent interactive runner in this logged-in desktop session.
.\run.cmd
```

Expected terminal state after startup: `Listening for Jobs`.

Do not install/start it as a Windows service for Stage-10 usability work; the workflow explicitly requires an interactive user session and foreground browser/hotkey behavior.

## Safety / invariants

- Fake-worker only. No real ChatGPT account yet.
- Manual `Ctrl+V` + Enter boundary remains frozen.
- No automatic paste/typing/Enter/Send.
- No ChatGPT DOM/content/output inspection.
- No credential/cookie/token/profile-secret collection.
- Do not weaken hotkey, content-free evidence, fake-worker, process-ownership, or exact-head boundaries.
- Do not run the multi-hour Stage-09 target benchmark during current Stage-10 work.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Recover the exact branch/task state from GitHub first.
Treat the authoritative capsule, current branch head, exact validation evidence, and traceability artifact as authoritative.
Do not rely on previous conversation prose when it conflicts with durable evidence.
