<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-extract-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-extract-redesign-v1
- Title: Research Engine Mostly-Local EXTRACT Redesign v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Return to first principles on research-engine EXTRACT and identify, benchmark, and if justified implement a provenance-preserving mostly-local extraction architecture that makes STANDARD Codex a rare ambiguity/failure fallback rather than the default, while reusing accepted local document/VERIFY infrastructure and not repeating approaches already invalidated by durable evidence.

## Workflow

- Repository: workspace-control
- Path: workflows/evidence-first-solution-research.v1.json
- Checkpoint: a9041372c50bf1258daea2236a3e62542a115117

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 453f5aa3f1386f87dcb3a256de6f31496c5346a9
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 4ffd429086c76da9759de2a34bdf0bc0de21d522
- Remote verified: true

## Next safe action

HANDOFF_SAFE Wave-1 boundary. Do not redo architecture/retrieval implementation and do not trigger Lambda yet. Authoritative research-engine main is 4ffd429086c76da9759de2a34bdf0bc0de21d522 (PR #128 merged); exact frozen Wave-1 trigger candidate is OPEN PR #129 head 929e04bc171789f7bf3eaf2c1f37d4b801de6a9d with CI PASS, module blob 4dac18c4ac0b7754d604a60c46948bc2cc8f6772, workflow path .github/workflows/lambda-ci-local-extract-wave1.yml and workflow blob a5be693f750c481db21d86d239a505083aae40aa. PR #127 is closed/superseded and must not be merged. First audit workspace-control admission/provisioner contracts for the smallest new workload class model-eval-local-extract-wave1: preserve the already-validated gpu-heavy/model_eval_dual_gpu_v1 exact two-A4500 resource binding, promoted qwen3.5-4b model binding, expanded-runtime exact binding, read-only trusted model/runtime cache, non-scientific state effect, and generic gpu-heavy DENY. Unlike model-eval-dual-gpu, the exact trusted Wave-1 workflow deliberately downloads a pinned pypdf wheel and exact-SHA historical arXiv PDFs, so explicitly design/test the narrow public-payload network authority required instead of copying the dual lane's payload-offline network class. Bind admission to the exact workflow path/blob and `/lambda-ci-local-extract-wave1` command. Merge only green workspace-control changes, install/verify the exact resulting SHA on Lambda, then issue exactly one `/lambda-ci-local-extract-wave1 929e04bc171789f7bf3eaf2c1f37d4b801de6a9d` comment on PR #129. Follow that run through report plus final root cleanup receipt and stop Wave 1 on PROMISING/PARTIAL/REJECT; no production routing change, larger-model search, generic gpu-heavy enablement, or repeated tuning loop.

## Remaining work

- Wave 1 admission — add the smallest separately reviewed model-eval-local-extract-wave1 manifest/policy route for exact workflow blob a5be693f750c481db21d86d239a505083aae40aa and command /lambda-ci-local-extract-wave1, reusing the validated dual-GPU resource/model/runtime binding while explicitly reviewing the bounded public-payload network requirement. Do not enable generic gpu-heavy.
- Wave 1 host activation — merge green workspace-control admission, install the exact resulting workspace-control SHA on Lambda through the accepted bootstrap/install path, and verify only the intended workload class becomes live with control-plane health and zero residue.
- Wave 1 execution — while PR #129 remains at exact head 929e04bc171789f7bf3eaf2c1f37d4b801de6a9d, issue exactly one `/lambda-ci-local-extract-wave1 929e04bc171789f7bf3eaf2c1f37d4b801de6a9d` comment and follow only the resulting dedicated workflow. Do not rerun blindly after any partial/ambiguous execution.
- Wave 1 decision — read the report/artifact and final root receipt, evaluate all 9 papers / 71 historical evidence objects under the one fixed configuration, and stop this wave with PROMISING, PARTIAL, or REJECT. Do not change production EXTRACT/VERIFY routing, download/test a larger model, broaden gpu-heavy, or begin an open-ended prompt/hyperparameter search in this wave.
- After the Wave-1 decision only, decide whether measured residuals justify Phase 4 component/model escalation, teacher adaptation, VERIFY-boundary analysis, or eventual production integration.

## Blockers / gates

- Lambda admission gap: workspace-control live_enabled_workload_classes currently has cpu-test, gpu-small, model-eval-single-gpu, and model-eval-dual-gpu only. No manifest route or workload-policy entry exists for model-eval-local-extract-wave1, so PR #129 must not be triggered yet.
- Admission-design constraint: Wave-1 workflow blob a5be693f750c481db21d86d239a505083aae40aa intentionally performs bounded public payload acquisition (pinned pypdf wheel plus exact-SHA historical arXiv PDFs). It therefore cannot blindly clone model-eval-dual-gpu's GITHUB_CONTROL_PLANE_ONLY_PAYLOAD_OFFLINE network class. The smallest reviewed route must preserve exact promoted model/runtime/two-GPU authority while explicitly and fail-closedly authorizing only the public-payload behavior required by this trusted workflow. Generic gpu-heavy must remain DENY.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-extract-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
