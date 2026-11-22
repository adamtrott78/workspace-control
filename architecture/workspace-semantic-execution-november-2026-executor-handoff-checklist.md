# November 2026 Integrated v0 — Executor Handoff Checklist

**Parent task:** `workspace-semantic-execution-migration-v1`  
**Branch:** `workspace-semantic-execution-migration-v1`  
**Current durable integration head:** `e1e4778ad3583c817e25d0836964181b88cdd62a`  
**Exact-head validation:** Workspace Control #3075 PASS; Semantic Execution #375 PASS; Operator Bridge #648 PASS.  
**Deadline:** 2026-11-30.  
**Definition of done:** every mandatory requirement in `architecture/workspace-semantic-execution-november-2026-acceptance.v0.1.json` is PASS and the integrated review records explicit `PROMOTE_V0`.  
**Current machine-readable acceptance matrix:** 10 PASS / 12 PARTIAL / 1 BLOCKED / 9 PENDING. Do not silently promote matrix rows from checklist evidence; a formal E7 reconciliation is still required. The front-end-related rows INST-02, INST-03, INST-04 and INST-05 are already PASS; INST-06 remains PENDING because no bounded real-account Stage-12 calibration has completed.
**Current live semantic-host status:** Workspace Shell multirepo activation ACCEPTED at runtime `54ac65cbcd4211554710b8f8f4231c6c9554e3cc`; semantic execution `7c20097c5f177f23c16a765b95ce94d7161f0d29` independently verified; evaluator isolation ACCEPTED; exact fake-worker private-route round trip accepted with restoration of the preexisting Jupyter Serve state.
**Current Windows Operator front-end status:** **FUNCTIONALLY ACCEPTED.** On the validated `e1e4778a…` line the operator directly confirmed the complete manual loop: clean dedicated Firefox startup, Ctrl+Space opens/focuses a fresh Personalized Temporary Chat and closes the startup blank, clipboard staging works, a premature second Ctrl+Space alerts/refocuses and does not advance/minimize, plain Enter in the foreground prepared worker unlocks the loop, and the following no-work Ctrl+Space minimizes the dedicated Firefox window. Literal raw `@github` invocation in Personalized Temporary Chat is also empirically accepted. No automatic paste, typing, Enter, Send, DOM/page-content scraping, or credential automation was introduced.
**Current next hard gate:** **decision gate before D4.** Functional front-end work no longer blocks system proving. No reusable Stage-12 live authority exists. If the operator chooses to proceed, freeze an updated bounded real-account Stage-12 review/procedure against the current validated front-end head, validate it 3/3, obtain fresh explicit one-shot authority, then execute D4. After D4, E1–E3 are the first true whole-system proving run: live mixed `research-iterate`, mixed executors, and forced worker/session/process-loss recovery.
**Required operator convenience layer:** source for persistent current-user commands `wop-up`, `wop-down`, `wop-reset`, `wop-status`, `wop-self-test` is validated at `5839870b067af9c416099e096d29c614c5b8402b` (Workspace #3082 / Semantic #382 / Operator #655 PASS). Adam explicitly classified these commands as necessary before proceeding. One bounded Windows profile install/verification remains; it does not create live Stage-12 authority.
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
- [x] Preserve accepted behavior: Ctrl+Space -> Ctrl+V -> Enter -> Ctrl+Space; no tab search; while a prepared worker is awaiting human Enter, repeated scheduler presses refocus/alert and cannot advance; after Enter confirmation, normal dispatch resumes and READY=0 minimizes only WorkspaceWorkers Firefox.
- [x] **A6 — Close the functional production Windows front end / fast loop.**
  - [x] Dedicated persistent non-default Firefox profile retains ChatGPT authentication while sessionstore-only cleanup prevents obsolete worker-tab resurrection.
  - [x] Idle worker window starts on a clean blank/new-tab surface; first Ctrl+Space visibly opens/focuses a fresh Personalized Temporary Chat, closes only the exact startup blank, and stages the clipboard packet.
  - [x] Literal raw `@github` invocation works in Personalized Temporary Chat without Tab/click/autocomplete selection.
  - [x] Passive human-submit confirmation is fail-closed: before plain Enter is observed in the captured foreground worker Firefox window, another Ctrl+Space alerts/refocuses and cannot advance/minimize; after Enter, the next press resumes normal dispatch.
  - [x] Final durable implementation/bookkeeping head `e1e4778ad3583c817e25d0836964181b88cdd62a` passed Workspace #3075 / Semantic #375 / Operator #648, and the operator directly confirmed the complete sequence works.
- [x] **A7 — Install and accept persistent per-user convenience commands before D4.**
  - [x] Source `5839870b067af9c416099e096d29c614c5b8402b` installs current-user executable shims for the existing `wop` wrapper plus `wop-up`, `wop-down`, `wop-reset`, `wop-status`, and `wop-self-test`.
  - [x] `wop-self-test` is read-only: repository SHA, .NET 10, Node 24, Firefox availability, and runtime health only; it does not launch Firefox or mutate bridge state.
  - [x] Installer does not depend on PowerShell profile execution. It removes only the obsolete owned v1 profile block if present, then installs owned `.cmd` shims in `%LOCALAPPDATA%\Microsoft\WindowsApps` only when that exact directory already exists and is already on PATH. No PATH mutation, persistent execution-policy mutation, admin rights, service, scheduled task, credential store, browser-profile mutation, or authority widening.
  - [x] Exact-head validation: Workspace #3082 PASS; Semantic #382 PASS; Operator #655 PASS, including Windows PowerShell parse of the installer and the full Operator regression suite.
  - [x] **ACCEPTED ON WINDOWS:** current head `1dbf252f65c85cc6a0c7a6ec9240f3c9636b44dd` materialized directly; stale runtime cleanup PASS; legacy profile block REMOVED; command path/install PASS; persistent `wop-up`, `wop-down`, `wop-reset`, `wop-status`, `wop-self-test` resolve as applications; `wop-self-test` PASS with .NET 10.0.404 / Node v24.22.2 / Firefox discovered / runtime OFFLINE; `wop-status` reports OFFLINE.

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

### D. Live semantic/Instant host — activation and functional Windows front end complete; D4 live calibration is the next gated test

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
  - [x] Boundary preserved: do **not** bypass with generic shell, manual sidecar, arbitrary Tailscale commands, network-enabled Workspace Shell profile, or helper/root-policy widening. Current helper registry is empty and frozen Workspace Shell profiles deny network.
- [x] **D3 — Prove one exact-host fake-worker action/status/result round trip through the reviewed private route before touching a real ChatGPT account.**\n  - [x] Attempt 01 materialized exact authorized transaction `81166627…` and passed host/peer/login binding, then failed closed on `PREEXISTING_SERVE_CONFIG:TCP` before PostgreSQL, Serve mutation, or fake-worker execution. Existing Serve state preserved.\n  - [x] Read-only diagnostic proved HTTPS 443 root `/` -> `http://127.0.0.1:8888`, Funnel disabled; existing configuration remained unchanged.\n  - [x] Coexistence-safe v2 review candidate `429362c93314fa2e17809ea78b04c69d8c9c4e83` passed Workspace #2965 / Semantic #265 / Operator #538.\n  - [x] Operator explicitly approved v2 transaction `2a6f65de5681f000a4b69913979db21953ab36a6` / blob `beef1ade487e117e519b4cec1e9e4d43a36ead57`; fresh narrow Attempt-02 authority is recorded in `architecture/workspace-semantic-execution-private-route-activation-authority.v0.2.json`.
  - [x] Account-free/model-free/browser-free/GPU-free harness is frozen at `7c20097c…` and repository-green (#2904/#226/#504).
  - [x] Attempt 02 passed the real reviewed private route: status ready -> exact claim -> revalidate -> local-prepared -> immutable fake candidate -> independent validator -> process COMPLETED -> action COMPLETED -> session READY -> final ready=0/sent=0; exact preexisting Jupyter Serve state restored.
- [ ] **D4 — Run bounded Stage-12 real-account calibration with no widened browser permissions, DOM/content automation, credential workaround, or synthetic account interaction.**\n  - [x] Exact Stage-12 review candidate `646d6b09e029823f27f7764d5085da2b7d4af7b8` passed Workspace #2975 / Semantic #275 / Operator #548.\n  - [x] Final approval-gate head `93b9ba76e860c6d3e06dd7bb8d7a54193705470e` passed Workspace #2977 / Semantic #277 / Operator #550.\n  - [x] Candidate-result branch `worker-result-candidates-v1` is isolated from source/authority state and was verified at baseline `0bc1bc0e9e6859bac6fd4feba82dae5b8c6f28de`.\n  - [x] Operator explicitly approved exactly one live attempt; authority persistence `8e701073…` passed #2978/#278/#551.\n  - [x] **Attempt 01 FAILED CLOSED and consumed that authority.** Linux passed exact preflight, activated the reviewed private route, preserved Jupyter/Funnel invariants and reached `STAGE12_Q1_READY`; Windows had never started the pinned launcher because PowerShell remained at the multiline continuation prompt, so no isolated Firefox/managed worker existed and Q1 could not be serviced.\n  - [x] No Q1 candidate was published; `worker-result-candidates-v1` remained exactly at `0bc1bc0e…`.\n  - [x] Post-failure cleanup restored the host to tailnet-only `/ -> http://127.0.0.1:8888`; `/operator-bridge/v1` is absent and Funnel is disabled. Failure evidence is frozen in `architecture/workspace-semantic-execution-stage12-real-instant-attempt-01.v0.1.json`.\n  - [x] The original authority artifact is marked `CONSUMED_FAILED_STAGE12_ATTEMPT_01`; it authorizes no retry.\n  - [x] Fresh retry candidate/procedure v0.2 is frozen: executable source `b0466c03acb9d6b863df421e2c116c84bff312f6`, Linux v2 blob `962cf39d8e48d1aef2b4a8a7e099f3333ccc8eca`, procedure commit `7a99f4518d8f3ac97d8ee638ee36c1edef952ca2`. It requires the exact observed Windows-ready marker before `STAGE12_LIVE_AUTHORITY_CONSUMPTION_POINT=PASS`, rechecks candidate baseline, and verifies exact cleanup restoration.\n  - [x] Retry review candidate exact head `cae09bc6c97eb4dd689e10f320176a567afda194` passed Workspace #2989 / Semantic #289 / Operator #562 and is marked `VALIDATED_REVIEW_CANDIDATE_NOT_AUTHORITY`.\n  - [x] Fresh operator approval received for retry v0.2; exact single-attempt authority is recorded in `architecture/workspace-semantic-execution-stage12-real-instant-authority.v0.2.json`.\n  - [x] Authority v0.2 persistence head `449acef0…` passed Workspace #2992 / Semantic #292 / Operator #565.\n  - [x] Pre-live Windows setup then failed non-consumingly: local PowerShell execution policy rejected the exact pinned `.ps1` before launcher execution; Firefox did not start, Linux did not run, and candidate branch remained baseline.\n  - [x] Retry procedure/review v0.3 validated at exact head `6021af35944cf052c760c2645d53a89f276c2533`: Workspace #2994 / Semantic #294 / Operator #567 SUCCESS. Procedure blob `62d98d601b451621fd17a869149ed295f1f9ca9a`; executable bytes unchanged.\n  - [x] v0.3 authority was approved/validated but its pre-live dotnet PATH blocker occurred before live consumption.\n  - [x] v0.4 bounded .NET 10 repair validated at `752e0f81…` (#2998/#298/#571), with final validated review state `4e1beced…` (#2999/#299/#572).\n  - [x] Fresh operator approval received for v0.4.\n  - [x] v0.5 Windows pre-live setup failed non-consumingly after successful .NET build because `npm.cmd` was not resolvable.\n  - [x] v0.6 Node 24 repair validated at `91875eea…` (#3006/#306/#579) and final state `fba38cb2…` passed #3007/#307/#580.\n  - [x] Operator explicitly approved v0.6, but pre-authority exact-procedure inspection found malformed PowerShell; no v0.6 authority was created or consumed.
  - [x] v0.7 review-only command-construction repair validated at `215287bb…`: Workspace #3010 / Semantic #310 / Operator #583, including exact PowerShell parse on Windows.
  - [x] v0.7 final lifecycle-corrected state `8bc74726…` passed Workspace #3012 / Semantic #312 / Operator #585; no executable bytes changed.
  - [x] Approval-gate freeze `73f1c57a…` passed Workspace #3013 / Semantic #313 / Operator #586.\n  - [x] Fresh explicit operator approval received for exactly one v0.7 attempt; authority is bound to procedure blob `620e78f0…`.\n  - [x] v0.7 authority persistence `ac1ad67d…` passed Workspace #3014 / Semantic #314 / Operator #587.\n  - [x] v0.7 authority was invalidated unconsumed before execution after exact-byte audit found two literal backslashes before `${env:ProgramFiles(x86)}`.\n  - [x] v0.8 two-backslash repair `f0051fb3…` passed Workspace #3016 / Semantic #316 / Operator #589.\n  - [x] Final v0.8 review-state `fc292181…` passed Workspace #3017 / Semantic #317 / Operator #590.\n  - [x] Fresh explicit operator approval received for exactly one v0.8 attempt bound to procedure blob `58c714ba…`.\n  - [x] v0.8 authority persistence `26ca22ae…` passed Workspace #3018 / Semantic #318 / Operator #591.\n  - [x] The historical v0.8/v0.9/v1.0 retry chain is superseded by the validated v1.1 Windows fast-loop program; no historical unchecked retry step remains current.
  - [x] Functional Windows front-end prerequisite accepted on `e1e4778a…`: dedicated profile/session cleanup, fresh Temporary Chat creation/focus, startup-blank closure, clipboard staging, raw `@github`, human Enter gate, and no-work minimize all passed direct operator observation.
  - [x] Front-end safety boundary preserved: no automatic typing/paste/Enter/Send, no DOM/page-content/output scraping, no credential automation, no public/Funnel exposure, no browser-permission widening.
  - [ ] **CURRENT D4 GATE:** fresh v1.1 review/procedure is frozen against validated source `2f32513f97834da76287d2f948891b758d5194f5`, launcher blob `a4619bcc…`, unchanged Linux v3/harness bytes, and candidate baseline `0bc1bc0e…`. Validate that review exact-head 3/3; then stop for explicit single-attempt operator approval. No live authority exists yet.

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


## 2026-11-21 front-end closeout and current decision gate

The prior retry-by-retry Stage-12 chronology is intentionally collapsed here because its old unchecked `CURRENT GATE` entries were superseded and had become misleading. Exact historical evidence remains authoritative in the Stage-12 authority/review/attempt artifacts, the two task capsules, Git history, and CI runs.

- [x] Live semantic host/evaluator activation and hostile-worker isolation accepted.
- [x] Reviewed private Tailscale Serve route and exact fake-worker action/status/result round trip accepted; preexisting Jupyter Serve/Funnel state restored after the proof.
- [x] Earlier real-account Stage-12 attempts failed closed at bounded setup/foreground/startup gates; consumed authorities are non-reusable and no candidate result was silently accepted.
- [x] Windows-only fast-loop redesign isolated browser/operator defects from Linux/Tailscale/PostgreSQL and repaired them without widening authority.
- [x] Persistent dedicated Firefox profile accepted; default/daily Firefox profile remains untouched.
- [x] Verified-dead dev-runtime filesystem residue may be journaled/deferred only after exact process-tree cleanup passes; stale residue is not authoritative runtime state.
- [x] Firefox sessionstore-only cleanup prevents obsolete fake-worker/duplicate-tab restoration while retaining login cookies/profile state.
- [x] Visual hotkey lifecycle accepted: idle blank -> Ctrl+Space opens/focuses fresh Personalized Temporary Chat -> startup blank closes -> clipboard packet staged.
- [x] Literal raw `@github` invocation accepted in Personalized Temporary Chat without plugin UI selection.
- [x] Human-submit gate accepted: premature repeat Ctrl+Space before plain Enter alerts/refocuses and cannot advance/minimize; plain Enter while captured worker Firefox is foreground unlocks the next press; no-work then minimizes only the dedicated Firefox window.
- [x] Final functional front-end state is durable at `e1e4778ad3583c817e25d0836964181b88cdd62a` with Workspace #3075 / Semantic #375 / Operator #648 PASS and direct operator acceptance.
- [x] Required operator UX gate complete: persistent current-user shims installed and accepted on Windows; `wop-self-test` and `wop-status` PASS.
- [ ] **NEXT CRITICAL TEST IF CHOSEN — D4:** prepare a fresh, exact, single-attempt Stage-12 real-account calibration review/authority against the current front-end state; do not inherit or revive any consumed historical authority.
- [ ] **THEN E1–E3:** run the live mixed Research Engine `research-iterate` workflow, deliberately inject one worker/session/process loss, recover from durable state without manual reconstruction, and capture live resource/soak evidence.
- [ ] E4 economics remains dependent on calibrated allowance evidence; B4/Codex gates remain independent and must not be bypassed.
- [ ] E5–E8 remain final acceptance work: target UX-09 benchmark, provenance/authority/rollback audit, formal matrix reconciliation, and explicit `PROMOTE_V0` / `HOLD` / `REVISE`.

### Decision status

**Functional front end: DONE.**  
**Convenience aliases: DONE / WINDOWS ACCEPTED.**  
**Whole-system real-account proof: NOT DONE.**  
**No live Stage-12 authority currently exists.**  
**Do not start D4/E1 automatically; operator requested this checklist reconciliation first and will choose the next step afterward.**


### 2026-11-21 alias-install repair note

- [x] First profile-based alias installer at `3c606ac1…` was rejected by real Windows evidence despite CI source validation: its generated block contained an invalid PowerShell variable-colon interpolation, and Adam's machine policy blocks profile script loading.
- [x] No policy weakening was accepted. The profile-based persistence design is superseded.
- [x] Replacement `ca8b5983…` removes only the obsolete owned profile block, installs owned command shims in an already-existing current-user WindowsApps PATH directory, and invokes the reviewed driver with `-NoProfile` and per-process `-ExecutionPolicy Bypass`; it never changes persistent execution policy or PATH.
- [x] Windows install/acceptance complete on current durable head.


### 2026-11-21 exact-SHA transport hardening

- [x] Real Windows bootstrap exposed a local object-materialization defect: the legacy session-level `wop` wrapper fetched the branch and could resolve ancestor commit `ca8b5983…`, but checkout failed with `fatal: unable to read tree`, leaving the DevCheckout on the old broken installer.
- [x] Do not bootstrap A7 by asking the legacy wrapper to jump to an intermediate ancestor.
- [x] Source `5839870b067af9c416099e096d29c614c5b8402b` hardens the installed shim driver: shallow-fetch current branch head, use `FETCH_HEAD` when it matches the requested SHA, fetch the exact SHA only when needed, checkout `FETCH_HEAD`, and explicitly verify the commit tree exists.
- [x] Exact-head validation: Workspace #3082 PASS; Semantic #382 PASS; Operator #655 PASS.
- [x] Current-head bootstrap, shim installation, self-test and status verification completed successfully. No D4 authority was created.
