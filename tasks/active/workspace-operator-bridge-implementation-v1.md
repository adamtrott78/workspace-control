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
- Remote checkpoint: e857db554a0ec570435b9525a50a9f2d220a5eef
- Remote verified: true

## Next safe action

D4 V1.8 ARMED — exact authority tip e857db554a0ec570435b9525a50a9f2d220a5eef is exact-head 3/3 green (Workspace #3123 / Semantic #423 / Operator #696), branch-stable at last verification, authority architecture/workspace-semantic-execution-stage12-real-instant-authority.v1.8.json is PENDING_OPERATOR_WOP_EXECUTION, and the attempt is unconsumed. The accepted Workspace Operator Bridge frontend is frozen at a9532ca8b86b7839822939a970e16af1d4a41864 (src tree 51480cc44f62d661421e975e67af127ecd0b0417; workspace-operator-dev.ps1 blob ac035d2fc898274c32cad43954ce44c15b198207). The exact next operator action is `wop d4`; executing that command is the approval signal, so do NOT ask Adam for a separate approval. D4 starts the backend first, waits for Q1 readiness, then launches the exact A7 frontend from the interactive parent PowerShell (Start-Job is forbidden for the frontend). When Firefox launches and the backend is ready, service only the emitted READY stage with Ctrl+Space -> Ctrl+V -> Enter. Q2 must reuse the same managed conversation/session; Q3 must use a replacement session after the old generation is fenced. No silent retry after STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS.

## Remaining work

- LIVE INSTANT / D4 V1.8: run exactly one authorized `wop d4` attempt from the frozen handoff tip. Backend-first launch is required; exact A7 frontend must launch from the interactive parent PowerShell only. Service Q1/Q2/Q3 with Ctrl+Space -> Ctrl+V -> Enter only when the corresponding READY marker exists. No silent retry after consumption.
- D4 HUMAN SERVICE: Q1 READY -> Ctrl+Space -> Ctrl+V -> Enter; Q2_REUSE_READY -> same sequence in the same managed conversation/session; Q3_REPLACEMENT_READY -> same sequence using the replacement session after stale generation fencing. Do not manually relay worker output; immutable candidate publication/validation is automatic.
- LIVE RESEARCH PROVING: only after D4 PASS, run the agreed Research Engine research-iterate E1-E3 workload with mixed executors, one forced worker/session/process loss, durable recovery without manual reconstruction, and CPU/RAM/task/resource/soak evidence.

## Blockers / gates

- OPERATOR-ONLY LIVE START: v1.8 authority is already staged and validated; only Adam can initiate it by executing exact `wop d4` on Windows. That command itself is the approval signal. Until it is executed, authority remains pending/unconsumed. After the live consumption marker, success or failure consumes the attempt and any retry requires a fresh diagnosis/review/validation cycle.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-operator-bridge-implementation-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
