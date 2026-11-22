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
- Remote checkpoint: 3986cbcb547e71c99c008cc22aad463df8165954
- Remote verified: true

## Next safe action

D4 V1.9 REVIEW / CLEANUP GATE. v1.8 is consumed and non-reusable after a real Q1 remote-dispatch failure; do not rerun it. v1.9 orchestration candidate 3986cbcb547e71c99c008cc22aad463df8165954 is 3/3 green (#3125/#425/#698) and preserves the frozen A7 frontend exactly. Immediate operator-only action is `wop-down` then `wop-status` to clean the degraded v1.8 Windows runtime and require OFFLINE. This v1.9 review grants zero live authority. After cleanup evidence, freeze/validate the v1.9 review state and request fresh explicit one-shot approval before any live retry.

## Remaining work

- Record Windows v1.8 cleanup PASS/OFFLINE evidence.
- Validate/freeze D4 v1.9 review/procedure exact head with A7 bytes unchanged.
- Only after explicit approval, create and validate a fresh one-shot v1.9 authority.
- After D4 PASS, continue to Research Engine research-iterate E1–E3 proving.

## Blockers / gates

- WINDOWS CLEANUP: current v1.8 helper runtime was observed DEGRADED (helper alive, web-ext/Firefox absent) and must be cleaned with accepted wop-down, then wop-status OFFLINE.
- LIVE AUTHORITY: v1.8 is consumed/non-reusable. v1.9 review candidate grants zero live authority; fresh exact-head validation and explicit one-shot approval are required.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
