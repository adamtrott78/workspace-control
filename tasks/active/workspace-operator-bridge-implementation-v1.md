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
- Remote checkpoint: 70f8c21185dad6dc0be8c84a21fe8fd841a557b6
- Remote verified: true

## Next safe action

D4 V1.14 CLEANUP-THEN-AUTHORITY GATE. v1.13 was consumed and failed after successful Q1 publication. Q1 candidate commit daa18627982a1d406eb88d44145113f0e99561e0 is valid, parent 7bab6ff…, and changed only worker-results/stage12/d85e6ca0d9484b4a98e8694e787d3505/q1.json. Live Operator Bridge diagnostic after Q1 was exactly readyManualCycles=0,sentUnconfirmed=1 for ~10 minutes: Q1 remained AWAITING_DURABLE_ACK and Q2 was never planned. A6 already proved literal raw @github works in Personalized Temporary Chat with autocomplete_selection_used=false and no Tab/click/autocomplete selection; A7 is the accepted frontend/convenience-command layer and must not be redesigned. v1.14 repair head 70f8c21185dad6dc0be8c84a21fe8fd841a557b6 passed Workspace #3153 / Semantic #455 / Operator #726. It restores literal @github in generated Stage12 packet objectives, changes CandidateWatcher to independently observe the candidate branch via git ls-remote then verify fetched visibility, emits STAGE12_Q1_CANDIDATE_OBSERVED=<sha> and STAGE12_Q1_DURABLE_INGEST=PASS, and advances candidate baseline to daa1862… without rewriting history. ZERO v1.14 live authority exists. First terminate/clean the still-running consumed v1.13 D4 runtime and prove Windows operator OFFLINE. After cleanup, create and exact-head validate exactly one fresh v1.14 authority; Adam already explicitly requested this repaired rerun in the handoff-preparation turn, so do not ask him to restate the same approval if the cleanup evidence is clean.

## Remaining work

- Terminate the consumed/stuck v1.13 D4 process and allow the remote transaction trap to restore Tailscale/PostgreSQL/runtime state.
- Run wop-down and verify wop-status reports WORKSPACE_OPERATOR_DEV_STATUS=OFFLINE.
- After cleanup evidence, stage and exact-head validate exactly one v1.14 authority bound to repair head 70f8c211…, candidate baseline daa1862…, repaired semantic backend, stale-route normalization, and unchanged A7.
- Run wop d4. Q1 packet must already contain literal @github; no manual edit and no Tab/click/autocomplete selection.
- Require STAGE12_Q1_CANDIDATE_OBSERVED=<new sha> then STAGE12_Q1_DURABLE_INGEST=PASS before STAGE12_Q2_REUSE_READY. If observation fails, the new fail-closed marker identifies remote/fetch visibility; if durable ingest fails, diagnosis is intake/state transition rather than browser/plugin UX.
- Complete Q2 same-chat continuity and Q3 replacement-session fencing. After D4 PASS, proceed to Research Engine research-iterate E1-E3.

## Blockers / gates

- CURRENT LIVE RUNTIME: consumed v1.13 is stuck after Q1 with readyManualCycles=0,sentUnconfirmed=1 and must be terminated/cleaned before another attempt.
- LIVE AUTHORITY: zero v1.14 authority exists until cleanup is proven and a fresh one-shot authority is created/validated.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
