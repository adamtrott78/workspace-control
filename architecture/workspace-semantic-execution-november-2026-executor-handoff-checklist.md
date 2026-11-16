# November 2026 Integrated v0 — Executor Handoff Checklist

**Parent task:** `workspace-semantic-execution-migration-v1`  
**Branch:** `workspace-semantic-execution-migration-v1`  
**Validated execution base before this handoff documentation:** `41d320100a0c2ee3890c900ed5295a94b08213af`  
**Validated workflows on that base:** Workspace Control #2849 PASS; Semantic Execution #178 PASS; Operator Bridge #437 PASS.  
**Deadline:** 2026-11-30.  
**Definition of done:** every mandatory requirement in `architecture/workspace-semantic-execution-november-2026-acceptance.v0.1.json` is PASS and the integrated review records explicit `PROMOTE_V0`.  
**Current acceptance matrix before this handoff commit:** 8 PASS / 13 PARTIAL / 1 BLOCKED / 10 PENDING.
**Current validated Stage-10 implementation checkpoint for this handoff:** `866e2805def9d7bb1e5640715a72c72efc895480` — Workspace #2885 PASS; Semantic #214 PASS; Operator Bridge #491 PASS; off-foreground UT-12 acceptance run #492 completed on the same exact head.
**Stage-10 human status:** COMPLETE. UT-05, UT-06, UT-07, UT-08, UT-12, UT-11 and UT-09 ACCEPTED; final hotkey disposition is **RETAIN Ctrl+Space**.

## Fresh-chat recovery protocol

1. Recover the exact GitHub head first. Trust the task capsules, this checklist, exact Git/CI/runtime evidence, and authority-owned policy over chat prose.
2. Verify the current `workspace-semantic-execution-migration-v1` head descends from `41d320100a0c2ee3890c900ed5295a94b08213af`. If it does not, reconcile before acting.
3. Read these authoritative children before choosing work:
   - `tasks/active/workspace-semantic-execution-backend-v1.json`
   - `tasks/active/workspace-operator-bridge-implementation-v1.json`
   - `tasks/active/workspace-reasoning-economy-v1.json`
   - Codex child `tasks/active/workspace-reasoning-economy-codex-runtime-v1.json` on its stacked branch when that lane is touched.
4. Keep Heartbeat on `workspace-semantic-execution-november-integration-plan-v1` while executing substantial work.
5. Continue autonomously through eligible repository work; stop only for a real authority/policy gate, stronger reasoning requirement, external wait, or genuinely user-only trial/action.

## DO NOT REDO — already implemented and validated

- [x] Durable ReasoningProcess/domain kernel and fail-closed transitions.
- [x] Recursive `TOO_LARGE` decomposition with inherited constraints/provenance/authority/validators and validated fan-in.
- [x] Durable distinction between `TOO_LARGE` and `INTRINSICALLY_DIFFICULT`.
- [x] Event-driven `WAIT_EXTERNAL` with no reasoning polling.
- [x] Deterministic packet compilation from typed durable state.
- [x] Persistent session broker, generation fencing, explicit replacement, transcript-independent recovery.
- [x] Durable OperatorAction lifecycle and backend action/status API.
- [x] Outbound HTTPS Windows Operator Bridge production client; no inbound Windows listener or app credential store.
- [x] Durable packet-source materialization with no packet text at rest.
- [x] Immutable worker-result/candidate publication and independent validation path; no ChatGPT-page scraping.
- [x] Repository-side Instant loop: scheduler -> HTTP claim -> local prepared -> immutable candidate -> intake -> validator -> completion.
- [x] PostgreSQL restart/idempotency/stale-generation coverage for the Instant loop.
- [x] Generic executor dispatch across deterministic exact-source and persistent Instant without model-name scheduler branches.
- [x] Mixed Research Engine `research-iterate` production-component proof: Instant decomposition -> deterministic exact-source read -> Instant analysis -> fan-in -> Instant synthesis.
- [x] Forced persistent-Instant session loss: stale old action/result fenced; replacement generation reconstructs from durable state and completes.
- [x] Production scheduler + explicit immutable GitHub candidate namespace at `0afd7837…`.
- [x] Scheduler stale-plan/replacement-session recovery and 1,000-cycle wait/no-poll soak at `d28b620e…` (#2843/#167/#431).
- [x] Weekly allowance governor at `65709645…` (#2844/#169/#432): reserve/headroom, burn projection, subscription-only routing, quality floors, matched holdout promotion logic.
- [x] Frozen Research Engine P0–P3 policy-trace adapter at `fadadcc0…`.
- [x] Controlled shared-allowance calibration harness at `59d69e0f…`: isolated actions + ordered snapshots; zero movement remains UNKNOWN/below-resolution; never derive allowance from raw tokens.
- [x] Claim-bearing runset promotion gate at `31f138a8…`: incomplete/superseded screening cannot become promotion evidence.
- [x] Reasoning Economy dispatch admission at `41d32010…` (#2849/#178/#437): governor may only choose among base-eligible executors; budget/meter denial occurs before process/session/action mutation.
- [x] Codex inert bootstrap implementation/static contract tests exist; do **not** implement another bootstrap workflow.

## ACTIVE AGENDA — execute in this order where gates allow

### A. Operator Bridge / Instant — immediate coding lane

- [x] **A1 — Implement Stage-10 harness support for UT-05 and UT-12 first.**
  - Implementation head `4c2e458f40bf205b70a293c02e1bde3b552bb254`.
  - Exact-head validation: Workspace Control #2853 PASS; Semantic Execution #182 PASS; Operator Bridge #441 PASS.
  - UT-05 has a distinct bounded judgment surface with zero judgment-phase clipboard/browser service effects; UT-12 has deterministic READY=0 + delayed background durable-ack evidence with zero clipboard/focus effects.
- [x] **A2 — Implement harness support for UT-06, UT-07, UT-08 recovery scenarios.**
  - Implementation head `3a075ebd05f16e34c754dbcc1600aa8fa620b04f`.
  - UT-06 uses managed-tab-loss fencing + exact generation advance; UT-07 uses auth-domain fencing + manual-auth return with no credential automation; UT-08 rehydrates a persisted cold-restart recovery incident before dispatch.
- [x] **A3 — Validate each coherent harness slice at exact head before asking the user to run it.**
  - Exact A2 validation: Workspace Control #2854 PASS; Semantic Execution #183 PASS; Operator Bridge #442 PASS.
- [x] **A4 — Complete remaining Stage-10 UT-12 acceptance; do not redo accepted recovery/judgment trials.**
  - [x] UT-05 accepted: #466 / job 132983488035; judgment popup foregrounded correctly, explicit Yes returned cleanly to Ctrl+Space -> Ctrl+V -> Enter, zero judgment-phase clipboard/browser effects.
  - [x] UT-06 accepted: #467 / job 132984929448; lost-worker recovery reached ReadyToResume with exact generation advancement and no wrong-worker/wrong-packet effects.
  - [x] UT-07 accepted: #480 / job 132995991788; auth-refresh recovery survives deliberate hesitation and native Windows foreground handoff visibly pulled Firefox forward from Discord; native foreground 1/1.
  - [x] UT-08 accepted: #481 / job 132997332383; durable cold-restart incident rehydrated and resumed with native foreground 1/1 and no wrong-worker/wrong-packet effects.
  - [x] UT-12 accepted after bounded trusted-HWND correction. Exact corrected head `866e2805def9d7bb1e5640715a72c72efc895480` passed Workspace #2885, Semantic #214 and Operator #491.
  - [x] Foreground-visible case #489 / job 133007524996: structured `OBJECTIVE_PASS`, minimize 1/1, delayed ack=1, zero no-work/background-ack clipboard or browser effects; operator confirmed Firefox minimized.
  - [x] Off-foreground case #492 / workflow 43778759491 / job 133010952603 on exact head `866e2805…`: structured `OBJECTIVE_PASS`, minimize 1/1, delayed ack=1, zero bridge clipboard/browser/focus effects, zero native foreground attempts, and zero wrong-worker/wrong-packet/rejected-state/dispatch failures.
  - [x] Operator deliberately focused another app on the second monitor and confirmed WorkspaceWorkers Firefox minimized while out of focus. The fix uses the already trusted captured Firefox HWND with `SW_SHOWMINNOACTIVE`; no arbitrary Firefox enumeration/minimization or authority widening was introduced.
- [x] **A5 — Finish final Stage-10 hotkey coverage.**
  - [x] Bridge-OFF UT-11 accepted from direct operator observation on validated head `b84f69cf…`: repeated Ctrl+Space produced no bridge reaction with Firefox focused or unfocused. Run #494 reached UT-11 ready state but was intentionally canceled; no completed OBJECTIVE_PASS is claimed from the canceled job.
  - [x] UT-09 representative-work collision gate accepted from accumulated real use: zero required native shortcut collisions remain for the operator's actual workflow, no meaningful interference is reported, and the identified VS Code Ctrl+Space function is not required by the operator.
  - [x] Final physical binding decision: **RETAIN Ctrl+Space**.
- [x] Preserve accepted behavior: Ctrl+Space -> Ctrl+V -> Enter; no tab search; repeated scheduler presses refocus/block pending action; READY=0 extra press minimizes only WorkspaceWorkers Firefox.

### B. Reasoning Economy — parallel, repository-safe lane

- [x] **B1 — Freeze completed P0–P3 screening and claim-bearing runset preparation.**
  - [x] Exact 20-run P0–P3/A–E screening completion manifest validated at `91dcc852…` (#2890/#219/#498).
  - [x] Exact 54-run scored-replicate plan validated at `9b02005a…` (#2891/#220/#499): 18 required arm×phenotype cells ×3 replicates.
  - [x] Superseded/refrozen-but-incomplete runs remain excluded from promotion evidence.
  - [x] Plan authorizes zero launches; scored runs are materialized only after admission.
- [x] **B2 — Preserve UNKNOWN allowance when no controlled comparable meter delta exists.** The frozen scored plan explicitly keeps the shared allowance relationship UNKNOWN and does not treat zero/absent movement as free.
- [x] **B3 — Do not rebuild governor / trace adapter / calibration harness / runset gate / dispatch admission.** Existing components remain the admission/promotion path.
- [ ] **B4 — When calibrated live traces exist, execute admitted scored replicates, exercise matched holdout promotion, and compare validated progress per scarce allowance against all-strong/frontier control.**
  - [x] Evaluator sealed-store primitive validated at `8470957f…` (#2897/#223/#501).
  - [x] Frozen 54-run plan now fail-closes on evaluator isolation at `74958b5d…` (#2899/#224/#502).
  - [ ] Before any claim-bearing launch, prove live hostile-worker read denial plus evaluator readback/commitment verification; repository mode/ownership tests alone are not sufficient.

### C. Codex subscription executor — authority-gated lane

- [ ] **C1 — Wait for lineage authority.** PR #627 is open draft at `acd420758eb0124646988ee8776939572c88a82d`; stacked PR #630 is open draft at `9d206a8f608ed86b416473e0ff66fabd99fea884`.
- [ ] **C2 — Do not bypass PR #627/#630** with manual runner creation, sidecar, generic root policy, PADataset/GPU borrowing, API billing, credits, or `OPENAI_API_KEY`.
- [ ] **C3 — Once lineage reaches reviewed/default-branch authority:** promote/bind the inert workflow blob, activate only through reviewed v3 authority, run zero-inference bootstrap.
- [ ] **C4 — If login absent, user performs one ChatGPT device-code authorization.**
- [ ] **C5 — Prove `account.type=chatgpt`, `planType=plus`, `OPENAI_API_KEY` absent, no API fallback, programmatic usage/rate-limit reads, zero model inference during bootstrap.
- [ ] **C6 — Run controlled isolated Codex/Instant calibration actions bracketed by official snapshots; only then feed real allowance observations into the governor.**

### D. Live semantic/Instant host — authority-gated lane

- [ ] **D1 — Do not activate while Workspace Shell semantic task authority is absent / TASK_NOT_FOUND.**
- [ ] **D2 — When exact reviewed/default-branch authority exists:** launch validated localhost backend and reviewed private Tailscale Serve route.
- [ ] **D3 — Prove one exact-host fake-worker action/status/result round trip before touching a real ChatGPT account.**
- [ ] **D4 — Then run bounded Stage-12 real-account calibration with no widened browser permissions, DOM/content automation, or security workaround.**

### E. Integrated live proving + final November acceptance

- [ ] **E1 — Run live mixed Research Engine `research-iterate`:** decomposition -> routing -> deterministic exact-source executor + Instant reasoning -> validated fan-in -> synthesis.
- [ ] **E2 — Inject at least one persistent-worker/session/process loss into that live run; recover from durable state without manual reconstruction.**
- [ ] **E3 — Capture live CPU/RAM/task/GPU-blind resource and soak evidence.**
- [ ] **E4 — Run calibrated economics comparison versus all-strong/frontier control.**
- [ ] **E5 — Run authoritative target-machine UX-09 performance benchmark.**
- [ ] **E6 — Mechanically check exact SHA/blob/route provenance, authority boundaries, rollback paths, and unresolved violations.**
- [ ] **E7 — Reconcile every requirement in the November acceptance matrix to PASS or record why promotion is impossible.**
- [ ] **E8 — Explicit integrated review: `PROMOTE_V0`, `HOLD`, or `REVISE`. November Integrated v0 is complete only on `PROMOTE_V0`.**

## Current gates / non-negotiable boundaries

- **Live semantic host:** suspended until Workspace Shell has exact reviewed authority for this task.
- **Codex:** suspended until PR #627/#630 lineage is trusted/promoted; subscription-only, no API billing.
- **Operator real account:** Stage-10 is complete; no Stage-12 until exact-host fake-worker transport is proven through reviewed live authority.
- **Frontier-equivalence claims:** remain blocked without evaluator-only isolation and claim-bearing replicated scoring.
- **GitRunner modernization:** deferred; do not rewrite/widen GitRunner authority from this task.
- **PADataset GPUs:** do not touch for this program; Workspace Control remains CPU-only control lane.

## Exact validated evidence worth preserving

- `d28b620e…`: Workspace #2843 / Semantic #167 / Operator #431 PASS — scheduler recovery + 1,000 wait/no-poll soak.
- `65709645…`: Workspace #2844 / Semantic #169 / Operator #432 PASS — weekly allowance governor.
- `fadadcc0…`: Workspace #2846 / Semantic #172 PASS — frozen policy-trace adapter; later descendants fully validate the ancestry.
- `59d69e0f…`: Workspace #2847 / Semantic #174 PASS — shared allowance calibration harness; later descendants fully validate the ancestry.
- `31f138a8…`: Workspace #2848 / Semantic #176 / Operator #436 PASS — claim-bearing runset gate.
- `41d320100a0c2ee3890c900ed5295a94b08213af`: Workspace #2849 / Semantic #178 / Operator #437 PASS — allowance admission integrated at dispatch.
- `91dcc852…`: Workspace #2890 / Semantic #219 / Operator #498 PASS — exact 20-run P0-P3/A-E protocol-screening completion manifest.
- `9b02005a…`: Workspace #2891 / Semantic #220 / Operator #499 PASS — exact 54-run claim-bearing scored-replicate/holdout plan frozen; zero launches authorized.

## Handoff behavior for the next executor

- Work from durable state, not conversation memory.
- Prefer connected GitHub/Workspace Shell evidence over asking the user to relay logs/SHAs.
- Keep Heartbeat current during long execution.
- Validate exact heads before promoting a milestone.
- Do not report implementation presence as live activation.
- Do not bypass authority gates.
- Continue through independent eligible lanes rather than waiting idly on Codex/live-host gates.
- Do not return merely because CI is running if another independent safe action exists.
- If blocked, state the exact gate and smallest authorized next action.
