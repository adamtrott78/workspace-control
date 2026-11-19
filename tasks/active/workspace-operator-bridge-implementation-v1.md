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
- Remote checkpoint: 093f85032abdd9ea336a9dcc2bb95eee948bac92
- Remote verified: true

## Next safe action

STAGE-12 FAST-LOOP IMPLEMENTATION CANDIDATE 093f8503… — prior synchronized head 21cefb25… passed Workspace #3039 and Semantic #339 but Operator #612 failed at compile before runtime because Program.cs used ?? across two different concrete action-port types. 093f8503… applies the one-line explicit IOperatorActionPort conditional repair. NEXT ACTION: exact-head validate the repaired synchronized implementation state; after 3/3 green, run the Windows-only synthetic smoke before any live Stage-12 retry.

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
