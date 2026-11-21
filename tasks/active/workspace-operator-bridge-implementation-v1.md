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
- Remote checkpoint: 7fcc1d4dc994d316b26316bdb9374295431aa36d
- Remote verified: true

## Next safe action

WINDOWS-ONLY SINGLE-TAB STARTUP SMOKE — repair 7fcc1d4dc994d316b26316bdb9374295431aa36d passed Workspace #3067 / Semantic #367 / Operator #640. The prior smoke reached the correct Personalized Temporary Chat but still restored a second ChatGPT tab from persistent Firefox session state, so the no-stray/duplicate gate failed before Ctrl+Space. 7fcc1d4d… keeps the dedicated persistent profile/login but forces browser.startup.page=0 and browser.sessionstore.resume_from_crash=false on both dev and real Stage-12 launches; the adapter then navigates the single blank startup tab to the fixed Temporary Chat URL. NEXT ACTION: run wop smoke on the current bookkeeping tip with no manual Firefox/tab cleanup. Require exactly one ChatGPT Temporary Chat tab, no Troubleshoot Mode prompt, retained auth or at most one login, then press Ctrl+Space once and verify clipboard exactly WORKSPACE_OPERATOR_SMOKE_PACKET_V1 plus managed Firefox foreground. Do not create or infer live Stage-12 authority from this local smoke.

## Remaining work

- live transport gate: after Workspace Shell semantic authority exists, prove exact-host Tailscale fake-worker transport before real-account use.
- impl_12: bounded real-account calibration with no DOM/content automation, no added browser permissions and no security workaround.
- impl_09: authoritative target-machine UX-09 performance/resource benchmark after real-account calibration.
- impl_13: explicit PROMOTE_V0/HOLD/REVISE production-readiness review.

## Blockers / gates

- The authoritative long-form UX-09 target benchmark remains intentionally SUSPENDED as an intermediate gate. It remains mandatory before impl_13 production readiness can pass.
- Real-account Stage-12 retry remains paused. Single-tab startup-policy repair 7fcc1d4d… is 3/3 validated, but the operator must rerun the Windows-only fast smoke and prove exactly one Personalized Temporary Chat tab before Ctrl+Space, then prove clipboard replacement and native foreground. No new live retry authority exists.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
