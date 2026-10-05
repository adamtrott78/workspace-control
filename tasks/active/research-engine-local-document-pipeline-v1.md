<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-document-pipeline-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-document-pipeline-v1
- Title: Research Engine Local Document Intelligence and Compute Offload v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Design, benchmark, and integrate a provenance-preserving local document-intelligence pipeline that converts content-addressed research PDFs into reusable LLM-ready paper packages, minimizes paid/plan semantic usage and repeated PDF interpretation, and systematically evaluates every research-engine stage for safe deterministic or local-model offload before production deployment on the Lambda.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 134d60630a1bf16499fee169f28456a670de343f
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 31d407abcf486e73d284cd66ddfe486ccab377a4
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 8a40b617cbdaf3d16e9ddeed41d6c9df9fbbb3db
- Local clean: true

## Next safe action

Do not rerun Qwen. The corrected guarded calibration on research-engine main@a72bc737ab22167af0b3ab7b95d01579810711e5 completed and returned FAIL_CLOSED_RETAIN_CODEX with 1/2 guarded jobs and 1/2 Codex-agreement jobs passing. Bounded VERIFY passed cleanly: page-2 VERIFY accepted exactly the three authoritative evidence IDs, returned verified=true/no issues, and matched STANDARD Codex exactly. Bounded EXTRACT failed closed because raw_source_form values at evidence indices 0,3,4,5,6,7 were not found on their cited authoritative page text after whitespace normalization; do not weaken this guard from the aggregate report alone. First inspect the already-existing successful-run qwen-results.json together with calibration-plan.json for EXTRACT job job:314b010cf54657c92d287ea3 and classify each miss as deterministic PDF/text representation drift versus actual paraphrase/fabrication. If and only if every miss is representation-only, implement the narrowest deterministic normalization and replay guard/adjudication over the saved outputs without model inference; otherwise retain Codex for EXTRACT. Do not rerun the completed calibration, visual benchmark, model boot, or C3 solely for telemetry. Natural Wave-3 evidence is R0=REUSED, R1=VERIFIED_HIT, R2=PRESENT_UNVERIFIED, R3=REUSED; total init 35.19516182200459 s vs 117.64840551599627 s cold, torch.compile 0.54 vs 18.17 s, profiling/warmup 0.77 vs 48.84 s, and vLLM internal init 17.41 vs 93.11 s. WAVE_3_FREEZE_READY=false because R2 is not explicitly verified and shared C3 has not naturally executed.

## Remaining work

- Do not rerun the completed guarded semantic calibration and do not rerun the visual benchmark. Preserve research-engine-daemon.service inactive/dead and keep Codex STANDARD as the production semantic baseline.
- Inspect the already-existing successful-run `qwen-results.json` and `calibration-plan.json` for EXTRACT job job:314b010cf54657c92d287ea3. Compare each failed raw_source_form (indices 0,3,4,5,6,7) against the exact cited-page text.
- Classify every EXTRACT grounding miss as either deterministic representation drift that can be normalized without changing lexical content (for example Unicode normalization/ligature/soft-hyphen/line-break artifacts) or genuine paraphrase/fabrication. Do not weaken the guard until this classification is evidence-backed.
- If all failed quotes are representation-only drift, implement the narrowest deterministic normalization necessary and replay only the guard/evaluation over the existing saved outputs; do not rerun Qwen. If any failed quote changes lexical content, retain Codex for EXTRACT and stop local EXTRACT promotion on this evidence.
- Open a separate production-integration decision for the validated bounded VERIFY residual class only after the EXTRACT diagnosis is recorded; do not silently retier all VERIFY jobs.
- Record natural Wave-3 adoption evidence as R0=REUSED, R1=VERIFIED_HIT, R2=PRESENT_UNVERIFIED, R3=REUSED with the observed timing improvements. Do not manufacture another boot or C3 call solely to turn R2/C3 green.
- When future owning scientific work naturally authorizes a same-modality canary and C4 in one live engine session, adopt the shared workspace-control C0-C4/operation receipt framework and reassess WAVE_3_FREEZE_READY.
- Retain the separate unresolved PP-OCRv6 scan-source replacement work after the Qwen semantic integration decision.

## Blockers / gates

- PP-OCRv6 remains resource-pass / quality-not-promoted; the blank scan target still requires replacement with a content-bearing image-only scan before scan-recovery promotion can be evaluated.
- PaddleOCR-VL-1.6 remains not promoted because of resource and semantic-quality failures; no further VLM family bakeoff is open.
- Qwen3.5-4B bounded VERIFY now has one successful guarded Qwen-vs-Codex calibration case and is a validated promotion candidate for that narrow residual class, but no production-routing change is authorized yet.
- Qwen3.5-4B bounded EXTRACT is not promoted: six returned raw_source_form fields failed exact page-grounding on the cited authoritative pages. Diagnose the already-existing qwen-results.json against calibration-plan.json before deciding whether this is deterministic PDF-text normalization or genuine Qwen paraphrase/fabrication.
- R2 compiled/JIT reuse remains PRESENT_UNVERIFIED despite large natural-boot timing reductions because the runtime log exposed no explicit reuse marker. Do not rerun solely to strengthen telemetry.
- Shared Wave-3 runtime_certified=true / WAVE_3_FREEZE_READY remain false until a naturally authorized C3 same-modality canary can share a live engine with C4; do not run C3 solely for telemetry.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
