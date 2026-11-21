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
- Remote checkpoint: ee3a21eef100539f36e7a0546f6d61e5f3bc3281
- Remote verified: true

## Next safe action

WINDOWS-ONLY SESSIONSTORE-RESET SMOKE — ee3a21eef100539f36e7a0546f6d61e5f3bc3281 passed Workspace #3072 / Semantic #372 / Operator #645. Previous smoke showed the old runtime closing correctly but Firefox sessionstore resurrecting the obsolete fake-worker URL; clipboard packet still loaded and the subsequent no-action alert was correct. ee3a21ee… clears only dedicated-profile tab/session restore artifacts before launch while retaining login/cookies. NEXT ACTION: run wop smoke on the current bookkeeping tip with no manual Firefox/tab cleanup. Before Ctrl+Space require exactly one blank/new-tab surface and no fake-worker page. Press Ctrl+Space once: require a fresh active https://chatgpt.com/?temporary-chat=true tab, Firefox foreground, startup blank closed, and clipboard exactly WORKSPACE_OPERATOR_SMOKE_PACKET_V1. Do not press a second time unless testing no-action behavior. No live Stage-12 authority exists.

## Remaining work

- live transport gate: after Workspace Shell semantic authority exists, prove exact-host Tailscale fake-worker transport before real-account use.
- impl_12: bounded real-account calibration with no DOM/content automation, no added browser permissions and no security workaround.
- impl_09: authoritative target-machine UX-09 performance/resource benchmark after real-account calibration.
- impl_13: explicit PROMOTE_V0/HOLD/REVISE production-readiness review.

## Blockers / gates

- The authoritative long-form UX-09 target benchmark remains intentionally SUSPENDED as an intermediate gate. It remains mandatory before impl_13 production readiness can pass.
- Real-account Stage-12 retry remains paused. Sessionstore reset ee3a21ee… is 3/3 validated, but operator must rerun Windows smoke and prove clean idle blank -> one Ctrl+Space fresh Personalized Temporary Chat/focus -> blank closed, with exact clipboard packet. No new live retry authority exists.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
