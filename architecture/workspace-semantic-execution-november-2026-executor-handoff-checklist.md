# November 2026 Integrated v0 — Executor Handoff Checklist

**Parent task:** `workspace-semantic-execution-migration-v1`  
**Branch:** `workspace-semantic-execution-migration-v1`  
**Validated execution base before this handoff documentation:** `41d320100a0c2ee3890c900ed5295a94b08213af`  
**Validated workflows on that base:** Workspace Control #2849 PASS; Semantic Execution #178 PASS; Operator Bridge #437 PASS.  
**Deadline:** 2026-11-30.  
**Definition of done:** every mandatory requirement in `architecture/workspace-semantic-execution-november-2026-acceptance.v0.1.json` is PASS and the integrated review records explicit `PROMOTE_V0`.  
**Current machine-readable acceptance matrix:** 10 PASS / 12 PARTIAL / 1 BLOCKED / 9 PENDING. This matrix still requires a formal reconciliation pass for the newly accepted live-host/evaluator evidence; do not infer additional PASS statuses until that reconciliation is committed.
**Current live semantic-host status:** Workspace Shell multirepo activation ACCEPTED at runtime `54ac65cbcd4211554710b8f8f4231c6c9554e3cc`; semantic execution `7c20097c5f177f23c16a765b95ce94d7161f0d29` independently verified; evaluator isolation ACCEPTED. Owning acceptance authority `05c7be116320ea8640b38870d622cf2b0023292e` passed Workspace #2945. Umbrella live-acceptance head `92325102e5730199a7735f09b17b8730a50d3185` passed Workspace #2946 / Semantic #241 / Operator #519.
**Current next hard gate:** execute the single explicitly authorized Stage-12 real-Instant calibration attempt under `architecture/workspace-semantic-execution-stage12-real-instant-authority.v0.1.json`. Authority persistence commit `8e701073484118344ee4f06816d3542ac0f0f7f7` passed Workspace #2978 / Semantic #278 / Operator #551. No Stage-12 live attempt has executed.
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

### D. Live semantic/Instant host — activation complete; private-route authority is the current gate

- [x] **D1 — Promote Workspace Shell semantic/evaluator runtime live and prove hostile-worker isolation.**
  - [x] Transactional activation completed with `LOCAL_CANDIDATE_MATERIALIZER_READY=PASS`, `LOCAL_SEMANTIC_TASK_RECEIPT=PASS`, `LOCAL_SEMANTIC_TASK_AUTHORITY=PASS`, `LOCAL_EVALUATOR_WORKER_DENIAL_RECEIPT=PASS`, `LOCAL_EVALUATOR_ISOLATION=PASS`, `EVALUATOR_ISOLATION_ACCEPTANCE=PASS`, and `WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS`.
  - [x] Live Workspace Shell runtime independently verified at `54ac65cbcd4211554710b8f8f4231c6c9554e3cc`; live semantic execution independently verified at frozen `7c20097c5f177f23c16a765b95ce94d7161f0d29`, exit 0, clean source.
  - [x] Activation semantic receipt: `job-d479bb9c-2ab2-4b01-b082-0921a173f0ac`; evaluator denial receipt: `job-0841ffee-e93e-4316-81a4-0a01a7d7bbfb`.
  - [x] Owning live-acceptance authority `05c7be116320ea8640b38870d622cf2b0023292e` passed Workspace #2945.
  - [x] Umbrella live-acceptance head `92325102e5730199a7735f09b17b8730a50d3185` passed Workspace #2946 / Semantic #241 / Operator #519.
- [x] **D2 — Establish explicit reviewed deployment authority for the localhost Operator Bridge backend + authenticated private Tailscale Serve route.**
  - [x] Non-authoritative activation proposal frozen at `a350fe07b25b4a67dc0ca714bb70633041c5b9e5`; Workspace #2950 / Semantic #245 / Operator #523 PASS.
  - [x] Proposed exact backend binding: `127.0.0.1:8765`, state key `control`, base path `/operator-bridge/v1`, private Tailscale Serve HTTPS only.
  - [x] Host review candidate `0668650142eb37fbd77f70b2983a30df17a03dc5` binds the exact private URL plus runtime-only Tailscale identity derivation, isolated temporary PostgreSQL DSN construction, and exact activation mechanism; Workspace #2958 / Semantic #256 / Operator #531 PASS.\n  - [x] Operator explicitly approved exact host-review `0668650142eb37fbd77f70b2983a30df17a03dc5` and transaction `8116662727003e9fe0904fa88ff7836608aeac00`; narrow durable authority is recorded in `architecture/workspace-semantic-execution-private-route-activation-authority.v0.1.json`.
  - [x] Transport design is already selected and validated: outbound-only HTTPS over authenticated tailnet; backend listens only on localhost; Tailscale Serve injects authenticated identity; no helper credential store; no public endpoint/Funnel.
  - [x] Production server composition and Windows HTTPS client are already repository-validated.
  - [x] Host-specific transaction candidate `8116662727003e9fe0904fa88ff7836608aeac00` / blob `765c846e7b6c1297f4a0a8871c2fdd34b453b5c2` freezes exact localhost port, runtime-only identity, isolated Postgres source, rollback, and fake-worker-only scope.\n  - [x] Tailnet `tailca6171.ts.net`, Linux `gokhan-lambda-vector`, Windows `desktop-ub9p70p`, MagicDNS ON, HTTPS certificates ON.
  - [ ] Do **not** bypass with generic shell, manual sidecar, arbitrary Tailscale commands, network-enabled Workspace Shell profile, or helper/root-policy widening. Current helper registry is empty and frozen Workspace Shell profiles deny network.
- [x] **D3 — Prove one exact-host fake-worker action/status/result round trip through the reviewed private route before touching a real ChatGPT account.**\n  - [x] Attempt 01 materialized exact authorized transaction `81166627…` and passed host/peer/login binding, then failed closed on `PREEXISTING_SERVE_CONFIG:TCP` before PostgreSQL, Serve mutation, or fake-worker execution. Existing Serve state preserved.\n  - [x] Read-only diagnostic proved HTTPS 443 root `/` -> `http://127.0.0.1:8888`, Funnel disabled; existing configuration remained unchanged.\n  - [x] Coexistence-safe v2 review candidate `429362c93314fa2e17809ea78b04c69d8c9c4e83` passed Workspace #2965 / Semantic #265 / Operator #538.\n  - [x] Operator explicitly approved v2 transaction `2a6f65de5681f000a4b69913979db21953ab36a6` / blob `beef1ade487e117e519b4cec1e9e4d43a36ead57`; fresh narrow Attempt-02 authority is recorded in `architecture/workspace-semantic-execution-private-route-activation-authority.v0.2.json`.
  - [x] Account-free/model-free/browser-free/GPU-free harness is frozen at `7c20097c…` and repository-green (#2904/#226/#504).
  - [x] Attempt 02 passed the real reviewed private route: status ready -> exact claim -> revalidate -> local-prepared -> immutable fake candidate -> independent validator -> process COMPLETED -> action COMPLETED -> session READY -> final ready=0/sent=0; exact preexisting Jupyter Serve state restored.
- [ ] **D4 — Run bounded Stage-12 real-account calibration with no widened browser permissions, DOM/content automation, credential workaround, or synthetic account interaction.**\n  - [x] Exact Stage-12 review candidate `646d6b09e029823f27f7764d5085da2b7d4af7b8` passed Workspace #2975 / Semantic #275 / Operator #548.\n  - [x] Final approval-gate head `93b9ba76e860c6d3e06dd7bb8d7a54193705470e` passed Workspace #2977 / Semantic #277 / Operator #550.\n  - [x] Candidate-result branch `worker-result-candidates-v1` is isolated from source/authority state and was verified at baseline `0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de`.\n  - [x] Operator explicitly approved exactly one live attempt; authority persistence `8e701073…` passed #2978/#278/#551.\n  - [x] **Attempt 01 FAILED CLOSED and consumed that authority.** Linux passed exact preflight, activated the reviewed private route, preserved Jupyter/Funnel invariants and reached `STAGE12_Q1_READY`; Windows had never started the pinned launcher because PowerShell remained at the multiline continuation prompt, so no isolated Firefox/managed worker existed and Q1 could not be serviced.\n  - [x] No Q1 candidate was published; `worker-result-candidates-v1` remained exactly at `0bc1bc0e…`.\n  - [x] Post-failure cleanup restored the host to tailnet-only `/ -> http://127.0.0.1:8888`; `/operator-bridge/v1` is absent and Funnel is disabled. Failure evidence is frozen in `architecture/workspace-semantic-execution-stage12-real-instant-attempt-01.v0.1.json`.\n  - [x] The original authority artifact is marked `CONSUMED_FAILED_STAGE12_ATTEMPT_01`; it authorizes no retry.\n  - [x] Fresh retry candidate/procedure v0.2 is frozen: executable source `b0466c03acb9d6b863df421e2c116c84bff312f6`, Linux v2 blob `962cf39d8e48d1aef2b4a8a7e099f3333ccc8eca`, procedure commit `7a99f4518d8f3ac97d8ee638ee36c1edef952ca2`. It requires the exact observed Windows-ready marker before `STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`, rechecks candidate baseline, and verifies exact cleanup restoration.\n  - [x] Retry review candidate exact head `cae09bc6c97eb4dd689e10f320176a567afda194` passed Workspace #2989 / Semantic #289 / Operator #562 and is marked `VALIDATED_REVIEW_CANDIDATE_NOT_AUTHORITY`.\n  - [x] Fresh operator approval received for retry v0.2; exact single-attempt authority is recorded in `architecture/workspace-semantic-execution-stage12-real-instant-authority.v0.2.json`.\n  - [x] Authority v0.2 persistence head `449acef0…` passed Workspace #2992 / Semantic #292 / Operator #565.\n  - [x] Pre-live Windows setup then failed non-consumingly: local PowerShell execution policy rejected the exact pinned `.ps1` before launcher execution; Firefox did not start, Linux did not run, and candidate branch remained baseline.\n  - [x] Retry procedure/review v0.3 validated at exact head `6021af35944cf052c760c2645d53a89f276c2533`: Workspace #2994 / Semantic #294 / Operator #567 SUCCESS. Procedure blob `62d98d601b451621fd17a869149ed295f1f9ca9a`; executable bytes unchanged.\n  - [x] v0.3 authority was approved/validated but its pre-live dotnet PATH blocker occurred before live consumption.\n  - [x] v0.4 bounded .NET 10 repair validated at `752e0f81…` (#2998/#298/#571), with final validated review state `4e1beced…` (#2999/#299/#572).\n  - [x] Fresh operator approval received for v0.4.\n  - [x] v0.5 Windows pre-live setup failed non-consumingly after successful .NET build because `npm.cmd` was not resolvable.\n  - [x] v0.6 Node 24 repair validated at `91875eea…` (#3006/#306/#579) and final state `fba38cb2…` passed #3007/#307/#580.\n  - [x] Operator explicitly approved v0.6, but pre-authority exact-procedure inspection found malformed PowerShell; no v0.6 authority was created or consumed.
  - [x] v0.7 review-only command-construction repair validated at `215287bb…`: Workspace #3010 / Semantic #310 / Operator #583, including exact PowerShell parse on Windows.
  - [x] v0.7 final lifecycle-corrected state `8bc74726…` passed Workspace #3012 / Semantic #312 / Operator #585; no executable bytes changed.
  - [x] Approval-gate freeze `73f1c57a…` passed Workspace #3013 / Semantic #313 / Operator #586.\n  - [x] Fresh explicit operator approval received for exactly one v0.7 attempt; authority is bound to procedure blob `620e78f0…`.\n  - [x] v0.7 authority persistence `ac1ad67d…` passed Workspace #3014 / Semantic #314 / Operator #587.\n  - [x] v0.7 authority was invalidated unconsumed before execution after exact-byte audit found two literal backslashes before `${env:ProgramFiles(x86)}`.\n  - [x] v0.8 two-backslash repair `f0051fb3…` passed Workspace #3016 / Semantic #316 / Operator #589.\n  - [x] Final v0.8 review-state `fc292181…` passed Workspace #3017 / Semantic #317 / Operator #590.\n  - [x] Fresh explicit operator approval received for exactly one v0.8 attempt bound to procedure blob `58c714ba…`.\n  - [x] v0.8 authority persistence `26ca22ae…` passed Workspace #3018 / Semantic #318 / Operator #591.\n  - [ ] **CURRENT GATE:** execute Windows v0.8 first; require `STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS` before Linux.

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

- **Workspace Shell semantic/evaluator activation:** COMPLETE and independently verified. Do not redo the activation sequence unless a real regression appears.
- **Private Operator Bridge route:** D3 COMPLETE. Attempt 02 passed full fake-worker transport and exact restoration of `/` -> `8888`; fake-worker authority is consumed.
- **Codex:** suspended until PR #627/#630 lineage is trusted/promoted; subscription-only, no API billing, no credits/API-key fallback.
- **Operator real account:** v0.8 one-shot authority is validated at `26ca22ae…` (#3018/#318/#591), bound to procedure blob `58c714ba…`. Windows is now the authorized next action. Linux remains blocked until `STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS`; live consumption remains at the reviewed Linux marker.
- **Reasoning Economy claim-bearing runs:** evaluator isolation gate is now satisfied live; launches still require reviewed live executor transport plus calibrated comparable weekly allowance telemetry. Do not manually grind the frozen 54-run matrix.
- **Frontier-equivalence / routing-promotion claims:** remain blocked until claim-bearing replicated scoring + matched holdout + calibrated allowance evidence exist.
- **GitRunner modernization:** deferred; do not rewrite/widen GitRunner authority from this task.
- **PADataset GPUs:** do not touch for this program; Workspace Control remains CPU-only control lane and the historical dirty PADataset checkout remains preserved.

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

- `299557f7…`: owning Workspace Shell handoff records the rollback-safe evaluator-denial `TARGET_PROFILE_DENIED` failure and pins the exact defect to `src/core.js::assertTargetProfile`; no activation success is claimed.


## 2026-11-16 live-host promotion closeout

- [x] Nine distinct rollback-safe activation defects were repaired without widening authority; the tenth activation passed end to end.
- [x] Materializer readiness, semantic exact-SHA execution, exact receipt binding, evaluator worker denial, sealed-store isolation, and transactional promotion all passed on the real host.
- [x] Post-activation independent receipts confirm the promoted runtime and frozen semantic execution remain exact and clean.
- [x] Private-route authority audit completed at `ab6b82df2e5886663f32b289a68939eed6be86f4`; Workspace #2947 / Semantic #242 / Operator #520 all PASS.
- [x] Exact v2 fake-worker transaction passed and restored `/` -> `8888` plus all preexisting relevant Serve/Funnel state.\n- [x] Operator explicitly approved validated Stage-12 candidate after final head `93b9ba76…` passed #2977/#277/#550; authority is single-attempt and exact.\n- [x] Authority persistence `8e701073…` passed #2978/#278/#551.\n- [x] Stage-12 Attempt 01 failed closed after Linux reached Q1 without a launched Windows managed worker; the one-shot authority is consumed, no candidate was published, and exact Jupyter/Funnel state was restored.\n- [x] Retry candidate/procedure v0.2 repaired and exact-head validated at `cae09bc6…` (#2989/#289/#562).\n- [x] Fresh explicit operator approval granted for retry v0.2 and narrow single-attempt authority artifact created.\n- [x] Authority v0.2 head `449acef0…` validated #2992/#292/#565; its first Windows pre-live setup failed before launcher execution and did not consume the attempt.\n- [x] v0.3 process-scoped execution-policy repair validated at `6021af35…` (#2994/#294/#567).\n- [x] Fresh explicit operator approval received for validated v0.3; single-attempt authority is recorded in `architecture/workspace-semantic-execution-stage12-real-instant-authority.v0.3.json`. v0.2 authority is superseded unconsumed/non-reusable.\n- [x] v0.3 authority persistence `6427c304…` passed Workspace #2996 / Semantic #296 / Operator #569.\n- [x] Windows v0.3 pre-live setup 02 failed non-consumingly after launcher start: `dotnet` was not resolvable from child PowerShell PATH; Firefox did not start and Linux did not run.\n- [x] v0.4 bounded .NET 10 discovery + temporary process-environment repair validated at `752e0f81…`: Workspace #2998 / Semantic #298 / Operator #571. Procedure blob `1d33484a…`.\n- [x] Fresh explicit operator approval received for validated v0.4; exact single-attempt authority is recorded in `architecture/workspace-semantic-execution-stage12-real-instant-authority.v0.4.json`. v0.3 is superseded unconsumed/non-reusable.\n- [x] v0.4 authority persistence `b7f65497…` passed Workspace #3000 / Semantic #300 / Operator #573.\n- [x] Windows v0.4 pre-live setup 03 failed non-consumingly with `DOTNET10_NOT_FOUND_IN_REVIEWED_LOCATIONS`; the reviewed list omitted the known working `%USERPROFILE%\.dotnet\dotnet.exe`.\n- [x] v0.5 user-profile .NET discovery repair validated at `c149c1aa…`: Workspace #3002 / Semantic #302 / Operator #575. Procedure blob `40049b88…`.\n- [x] Fresh explicit operator approval received for validated v0.5; exact single-attempt authority is recorded in `architecture/workspace-semantic-execution-stage12-real-instant-authority.v0.5.json`. v0.4 is superseded unconsumed/non-reusable.\n- [x] v0.5 authority persistence `f84195c5…` passed Workspace #3004 / Semantic #304 / Operator #577.\n- [x] Windows v0.5 pre-live setup 04 failed non-consumingly after successful .NET build because `npm.cmd` was not resolvable from the child PowerShell environment.\n- [x] v0.6 Node 24 runner-tool-cache repair validated at `91875eea…`: Workspace #3006 / Semantic #306 / Operator #579. Procedure blob `dd995d97…`.\n- [x] Operator explicitly approved v0.6 with `DO IT`, but exact pre-authority inspection invalidated procedure blob `dd995d97…`; no v0.6 authority artifact was created and no live action ran.
- [x] v0.7 review-only repair validated at `215287bb…` (#3010/#310/#583); exact fenced PowerShell parses successfully on the Windows Operator validator.
- [x] Final lifecycle-corrected v0.7 state `8bc74726…` passed Workspace #3012 / Semantic #312 / Operator #585.
- [x] Approval-gate freeze `73f1c57a…` passed Workspace #3013 / Semantic #313 / Operator #586.\n- [x] Fresh explicit v0.7 approval received; exact one-shot authority is being persisted and v0.5 is superseded unconsumed/non-reusable.\n- [x] v0.7 authority persistence `ac1ad67d…` passed Workspace #3014 / Semantic #314 / Operator #587.\n- [x] v0.7 invalidated unconsumed before any Windows/Linux execution; live marker not reached.\n- [x] v0.8 review-only repair `f0051fb3…` passed Workspace #3016 / Semantic #316 / Operator #589.\n- [x] Final v0.8 review-state `fc292181…` passed Workspace #3017 / Semantic #317 / Operator #590.\n- [x] Fresh explicit v0.8 approval received; exact one-shot authority is being persisted.\n- [x] v0.8 authority persistence `26ca22ae…` passed Workspace #3018 / Semantic #318 / Operator #591.\n- [x] Windows v0.8 pre-live run reached `STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS`, then cleaned up before Linux; `STAGE12_WINDOWS_CLEANUP=PASS` confirms a non-consuming pre-live abort.\n- [ ] **CURRENT GATE:** restart the exact unchanged Windows v0.8 procedure; after manual auth + Instant press Enter once, then leave the final cleanup prompt waiting while Linux runs.

- [x] 2026-11-18 v0.8 pre-live cleanup abort 01: no Linux live marker, candidate branch stayed `0bc1bc0e…`, authority remains unconsumed.

- [x] 2026-11-18 v0.8 restart cleanup 02: Firefox-open guard failed closed; after manual Firefox close, stale `%TEMP%\workspace-control-stage12-retry-v7` blocked rerun. No Linux/live marker; authority remains unconsumed.
- [ ] Remove only the exact stale temp staging directory under fail-closed cleanup authority, then rerun the exact unchanged Windows v0.8 command with Firefox closed.

- [x] 2026-11-18 v0.8 Windows ready gate re-established: `STAGE12_WINDOWS_MANUAL_AUTH_AND_INSTANT_CONFIRMED=PASS`; PowerShell held at final cleanup prompt; e6e24ee0… passed #3021/#321/#594; candidate baseline unchanged.
- [ ] Run exact Linux v2 transaction from source `b0466c03…`, verify blob `962cf39d…`, then type the exact Windows-ready marker at the Linux gate. Live authority is consumed only when Linux prints `STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`.

- [x] 2026-11-18 v0.8 Linux pre-live failed non-consumingly: exact v2 blob `962cf39d…` hit `REPO_URL: unbound variable` before the live marker; exact audit found three literal `\\n` sequences joining four declarations.
- [x] v0.8 authority invalidated unconsumed/non-reusable; changed Linux bytes cannot inherit it.
- [ ] v0.9 review-only Linux v3 candidate `3eb352f4…` changes only those three literal newline sequences to real LF bytes; validate 3/3, persist final review state, then obtain fresh explicit approval.

- [x] v0.9 Linux declaration repair exact candidate `efaf5170…` passed Workspace #3024 / Semantic #324 / Operator #597.
- [ ] **CURRENT GATE:** validate final v0.9 review-state persistence 3/3, then request fresh explicit v0.9 approval; v0.8 authority is not reusable.

- [x] Fresh explicit v0.9 approval received: `pls go yes authorize fuck`; binds final review head `a84eb08e…`, review `de0139b…`, procedure `5113b2e7…`, Linux v3 `3eb352f4…`, unchanged harness/launcher, candidate baseline `0bc1bc0e…`.
- [ ] Validate v0.9 authority-persistence head 3/3 before any Windows/Linux execution.

- [x] v0.9 authority persistence `b3798222…` passed Workspace #3026 / Semantic #326 / Operator #599; authority blob `f08bdab3…` is validated for exactly one live attempt.
- [ ] Re-establish fresh Windows v0.9 pre-live runtime; if old v0.8 cleanup prompt is still open, clean it first. Leave the new final cleanup prompt waiting after the Windows-ready marker.

- [x] 2026-11-18 v0.9 Windows pre-live cleanup abort 02: final cleanup prompt was submitted before Linux; launcher cleanup PASS, outer temp deletion raced on `SharedContracts.dll`; no live consumption marker; authority remains unconsumed.
- [ ] Bounded stale-stage cleanup, then rerun exact unchanged v0.9 Windows command. At final cleanup prompt, do **not** press Enter until Linux reports Stage-12 result.

- [x] Stage-12 v0.9 live authority consumed at `STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`; Q1 exposed Windows foreground activation defect. No Q1 candidate accepted; v0.9 non-reusable.
- [ ] Validate bounded foreground-fallback repair candidate: LocalPrepared hotkey path must invoke existing Win32 `ForegroundPreparedWorkerWindow()` before `RecordPreparedWorkerWindow()`.
- [ ] After candidate validation, freeze fresh retry review/procedure and obtain new explicit operator approval before any live retry.

- [x] Foreground repair code candidate `1ecc094a…` passed Workspace #3030 / Semantic #330 / Operator #603.
- [x] Freeze v1.0 review/procedure: foreground fallback blob `2e0d2248…`, procedure `9a43ba28…`, review `680596a3…`; no live authority.
- [ ] Exact-head validate v1.0 review-state persistence 3/3.
- [ ] Verify consumed v0.9 Linux route restoration + Windows/stale-stage cleanup before requesting v1.0 live approval.

- [x] v1.0 review-state `ecdc71c8…` passed Workspace #3031 / Semantic #331 / Operator #604; review remains non-authoritative.
- [ ] Exact-head validate v1.0 validation-state persistence 3/3.
- [ ] Verify v0.9 Linux route restoration + Windows/stale-stage cleanup before requesting v1.0 approval.

- [x] v1.0 validation-state persistence `bd366f93…` passed Workspace #3032 / Semantic #332 / Operator #605; review remains non-authoritative.
- [ ] Verify consumed v0.9 predecessor cleanup: exact Linux Tailscale restoration + temporary Postgres stop, Windows helper/Firefox cleanup, and stale Stage-12 temp directory removal.
- [ ] Only after cleanup evidence: request fresh explicit v1.0 approval.

- [x] FINAL HANDOFF BASIS: `7b5b7bc2…` passed Workspace #3033 / Semantic #333 / Operator #606; v1.0 review remains validated non-authority.
- [x] PREDECESSOR CLEANUP GATE: exact `STAGE12_V09_LINUX_CLEANUP_VERIFIED=PASS` and `STAGE12_V09_WINDOWS_CLEANUP_VERIFIED=PASS` observed from bounded operator cleanup on 2026-11-19.
- [x] CLEANUP-CLOSURE VALIDATION GATE: `a0a4db44…` passed Workspace #3035 / Semantic #335 / Operator #608.\n- [x] Fresh explicit v1.0 approval received: `christ ofc i approve it GO`; binds procedure `9a43ba28…`, review `e525b37d…`, foreground source `1ecc094a…` / blob `2e0d2248…`, Linux v3 `3eb352f4…`, harness `7b1feb8f…`, launcher `d9d474ca…`, candidate baseline `0bc1bc0e…`.\n- [ ] AUTHORITY-PERSISTENCE GATE: exact-head validate v1.0 authority state with Workspace/Semantic/Operator 3/3 before any Windows/Linux execution.\n- [ ] After authority persistence is 3/3 green, run exact Windows-first v1.0 pre-live setup and leave its final cleanup prompt untouched while Linux runs.


- [x] Stage-12 v1.0 authority persistence `b8189516…` passed Workspace #3036 / Semantic #336 / Operator #609.
- [x] Stage-12 v1.0 live authority consumed at `STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`; Q1 failed before dispatch because bridge startup remained OFF and Ctrl+Space was not globally registered. Candidate branch remained `0bc1bc0e…`.
- [x] Root cause audit: `BridgeController.SetEnabled(true)` is only reached by the manual tray toggle in current runtime; Program/Stage-12 launcher do not enable it. Clipboard/focus/native-foreground paths were not exercised.
- [x] Freeze v1.1 fast-loop review/procedure: explicit start-enabled mode, Windows-only synthetic local smoke, one-command start/stop/reset/status/smoke dev lifecycle, production bounded supervisor direction.
- [ ] CURRENT GATE: explicit operator approval for the exact v1.1 source mutation scope recorded in `architecture/workspace-semantic-execution-stage12-fast-loop-review.v1.1.json`; current task mutation scope does not authorize `operator-bridge/src/**` or `operator-bridge/tools/**`.
- [ ] After source-scope approval, implement + CI-validate the Windows-only smoke path before creating any new Stage-12 live authority.
