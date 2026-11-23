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
- Remote checkpoint: 48c5fcfa5b0a7312b6d944819c559858cb41a3a0
- Remote verified: true

## Next safe action

D4 V1.10 EXPLICIT ONE-SHOT APPROVAL GATE. v1.9 is consumed and non-reusable. Root cause is validated and repaired backend-only: .NET PostAsJsonAsync chunked request bodies versus the former Content-Length-only backend reader. Repair 020d35156d90e8268fb560a10e67098a146880de passed Workspace #3132 / Semantic #434 / Operator #705; frozen v1.10 review 0d74dc4b7562faef60e9e8c1b9748691ec596963 passed #3133/#435/#706; cleanup-gate bookkeeping 48c5fcfa5b0a7312b6d944819c559858cb41a3a0 passed #3134/#436/#707. Windows cleanup is accepted because wop-down emitted WORKSPACE_OPERATOR_DEV_OFFLINE=PASS and wop-status emitted WORKSPACE_OPERATOR_DEV_STATUS=OFFLINE, and the harness explicitly emits only DEV_OFFLINE when runtime.json is already absent. Accepted A7 bytes remain unchanged. ZERO live authority exists. Stop until Adam freshly and explicitly approves exactly one v1.10 D4 attempt. After approval only, create a fresh v1.10 one-shot authority bound to the validated repair/review/source, exact-head validate it, then execute one bounded live attempt. No silent retry.

## Remaining work

- Wait for Adam's fresh explicit approval of exactly one v1.10 D4 attempt.
- After approval only, create and exact-head validate a fresh one-shot v1.10 authority bound to the validated chunked-POST backend repair and unchanged A7 frontend.
- Execute exactly one bounded v1.10 D4 attempt.
- After D4 PASS, proceed to Research Engine research-iterate E1–E3 proving.

## Blockers / gates

- LIVE AUTHORITY: v1.10 repair/review and Windows cleanup are accepted, but the review grants zero live authority. Fresh explicit approval for exactly one v1.10 D4 attempt is required.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
