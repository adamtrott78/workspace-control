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
- Remote checkpoint: 9f21d300efc9a82db358bd636b53f51e73a47946
- Remote verified: true

## Next safe action

D4 V1.13 EXPLICIT ONE-SHOT APPROVAL GATE. v1.12 aborted pre-consumption after STAGE12_CANDIDATE_BASELINE=PASS because an exact stale Stage12 Tailscale route was still present; semantic live binding and the live consumption marker were never reached, so v1.12 is superseded/non-reusable but unconsumed. v1.13 fixes the preflight ordering and normalizes only the exact /operator-bridge/v1 -> 127.0.0.1:8765/operator-bridge/v1 route, and only after proving port 8765 has no listener; arbitrary Serve/Funnel drift still fails closed. Candidate head 534ff64254643346551a9d17a402f8cc4ff84b07 passed Workspace #3148 / Semantic #450 / Operator #721. Frozen v1.13 review head 9f21d300efc9a82db358bd636b53f51e73a47946 passed Workspace #3149 / Semantic #451 / Operator #722. Candidate baseline 7bab6ff5…, semantic repair 020d35156… / backend blob 3b6893c1…, and A7 remain unchanged. ZERO v1.13 live authority exists. Stop until Adam freshly and explicitly approves exactly one v1.13 D4 attempt. After approval only, create and exact-head validate one fresh authority; require candidate baseline PASS, exact stale-route normalization/clean root state, and STAGE12_SEMANTIC_LIVE_BINDING=PASS before consumption.

## Remaining work

- Wait for Adam's fresh explicit approval of exactly one v1.13 D4 attempt.
- After approval only, create and exact-head validate a fresh one-shot v1.13 authority bound to the exact stale-route normalization, candidate baseline 7bab6ff5…, semantic repair 020d35156… / backend blob 3b6893c1…, and unchanged A7.
- Execute exactly one bounded v1.13 D4 attempt. STAGE12_CANDIDATE_BASELINE=PASS, any required TAILSCALE_STALE_STAGE12_ROUTE_CLEARED=PASS, TAILSCALE_STAGE12_ROUTE_ABSENT=PASS, and STAGE12_SEMANTIC_LIVE_BINDING=PASS must occur before STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS.
- After D4 PASS, proceed to Research Engine research-iterate E1–E3 proving.

## Blockers / gates

- LIVE AUTHORITY: v1.13 repair and frozen review are exact-head validated, but zero live authority exists. Fresh explicit approval for exactly one v1.13 D4 attempt is required.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
