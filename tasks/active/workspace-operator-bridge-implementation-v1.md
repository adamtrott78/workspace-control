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
- Remote checkpoint: 5bcd6dada98c2e55d2c310e2a9f8caae74ca7ad2
- Remote verified: true

## Next safe action

D4 V1.12 EXPLICIT ONE-SHOT APPROVAL GATE. v1.11 aborted pre-consumption on a stale candidate-baseline guard and is superseded/non-reusable; no live authority was consumed. The isolated worker-result-candidates-v1 branch legitimately advanced from initialization 0bc1bc0e… to 7bab6ff5… by exactly one Q1 RESULT commit at worker-results/stage12/5dda87…/q1.json. v1.12 preserves that immutable history and binds the reviewed current candidate head 7bab6ff5… in the Stage12 preflight; the in-harness CandidateWatcher still requires each new quantum to be exactly one commit with the expected path. Repair head 60fd1e3f2bfcbbd92ba2a75d0208cbdf1bd00f4e passed Workspace #3144 / Semantic #446 / Operator #717. Frozen v1.12 review head 5bcd6dada98c2e55d2c310e2a9f8caae74ca7ad2 passed Workspace #3145 / Semantic #447 / Operator #718. The v1.11 live semantic repair remains bound (SEMANTIC_SHA 020d35156… / operator HTTP blob 3b6893c1…) and A7 remains unchanged. ZERO v1.12 live authority exists. Stop until Adam freshly and explicitly approves exactly one v1.12 D4 attempt. After approval only, create and exact-head validate one fresh authority; require candidate baseline PASS and STAGE12_SEMANTIC_LIVE_BINDING=PASS before the consumption marker.

## Remaining work

- Wait for Adam's fresh explicit approval of exactly one v1.12 D4 attempt.
- After approval only, create and exact-head validate a fresh one-shot v1.12 authority bound to candidate baseline 7bab6ff5…, live semantic SHA 020d35156… / backend blob 3b6893c1…, and unchanged A7.
- Execute exactly one bounded v1.12 D4 attempt. Candidate-baseline PASS and STAGE12_SEMANTIC_LIVE_BINDING=PASS must occur before STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS.
- After D4 PASS, proceed to Research Engine research-iterate E1–E3 proving.

## Blockers / gates

- LIVE AUTHORITY: v1.12 repair and frozen review are exact-head validated, but zero live authority exists. Fresh explicit approval for exactly one v1.12 D4 attempt is required.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
