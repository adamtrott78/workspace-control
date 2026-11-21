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
- Remote checkpoint: b749417849914c395bef5ac267b3c385edbdff04
- Remote verified: true

## Next safe action

WINDOWS-ONLY RESIDUE-DEFER RECOVERY SMOKE — source b7494178… passed Workspace #3063 / Semantic #363 / Operator #636. The retry on bookkeeping tip d9e3bee1… proved runtime-owned process cleanup with WORKSPACE_OPERATOR_RUNTIME_PROCESS_CLEANUP=PASS, but the old run-ee58… directory still could not be deleted and teardown stopped at DEV_RUNTIME_CLEANUP_FAILED. This proves the remaining blocker is filesystem residue after owned processes are dead. b7494178… journals an undeletable verified-dead workdir to cleanup-residue.jsonl, clears old state/registry binding, emits WORKSPACE_OPERATOR_RUNTIME_WORKDIR_CLEANUP=DEFERRED, and continues startup with a fresh GUID runtime. NEXT ACTION: run wop smoke on the current bookkeeping tip; no manual cleanup first. Verify stale residue is deferred rather than fatal, then persistent Temporary Chat/login + Ctrl+Space/clipboard/focus still pass.

## Remaining work

- live transport gate: after Workspace Shell semantic authority exists, prove exact-host Tailscale fake-worker transport before real-account use.
- impl_12: bounded real-account calibration with no DOM/content automation, no added browser permissions and no security workaround.
- impl_09: authoritative target-machine UX-09 performance/resource benchmark after real-account calibration.
- impl_13: explicit PROMOTE_V0/HOLD/REVISE production-readiness review.

## Blockers / gates

- The authoritative long-form UX-09 target benchmark remains intentionally SUSPENDED as an intermediate gate. It remains mandatory before impl_13 production readiness can pass.
- Real-account Stage-12 retry is paused until the Windows-only fast smoke proves global Ctrl+Space registration, clipboard replacement, Firefox focus, and native foreground behavior. No new live retry authority exists.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
