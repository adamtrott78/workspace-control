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
- Remote checkpoint: a69bb92d99bffc4e6df05ed59809cbdddff61f0a
- Remote verified: true

## Next safe action

WINDOWS-ONLY FAST SMOKE GATE — runtime-guard/build-cache source a69bb92d… passed Workspace #3048 / Semantic #348 / Operator #621. The first eac272f9… smoke never launched because the obsolete existing-Firefox guard fired after build. That guard is removed, Test-Pid uses $ProcessId, and repeat runs cache the .NET build by operator-bridge/src tree. NEXT ACTION: operator runs `wop smoke a69bb92d99bffc4e6df05ed59809cbdddff61f0a`, then presses Ctrl+Space once. PASS requires clipboard exactly WORKSPACE_OPERATOR_SMOKE_PACKET_V1 and the dedicated Firefox window foregrounded. No Linux/Tailscale/PostgreSQL/live authority is involved.

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
