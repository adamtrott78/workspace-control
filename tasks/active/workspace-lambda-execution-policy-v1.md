<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-lambda-execution-policy-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-lambda-execution-policy-v1
- Title: Workspace Lambda Execution Policy and Model Workload Governance v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Design, implement, and adversarially validate a fail-closed workload admission, trusted model/dependency cache, resource-governance, and execution-evidence layer on top of the accepted Lambda P5 CPU and gpu-small autonomous runner substrate so ChatGPT/GitHub-driven work can safely execute pinned model-scale workloads without granting candidate workflow code the ability to invent capabilities, persist mutable cross-job state, access production/scientific state, or widen host authority.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: effc5b2f39fe897f4b9dc9fe6767d2002ee81cdb
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: fa0ff6f1a4a46fd0295e45df401aa8361d220c86
- Remote verified: true

## Next safe action

Install exact workspace-control SHA effc5b2f39fe897f4b9dc9fe6767d2002ee81cdb on the Lambda host using the existing authorized P5 bootstrap and verify runtime blob 4615bcb7a06253186b61d31688f7720b45e760f0 plus installed trusted CUDA OOM probe blob 046f614508dd6b5f7cab981fc803a20ea33dcbf6 at /opt/workspace-ci/provisioner/trusted-probes/lambda_ci_cuda_oom_probe.py, root-owned and non-writable. Then run one root-authored synthetic gpu-small CUDA OOM host canary only on accepted GPU UUID GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea. Do not submit a GitHub job; do not use candidate payload code; do not load model weights or perform inference. The synthetic launch spec may add trusted_failure_probe only after ordinary validated gpu-small spec construction, with kind=cuda_oom_acceptance_v1, authority=ROOT_SYNTHETIC_CANARY_ONLY, exact installed path, source_blob_sha=046f614508dd6b5f7cab981fc803a20ea33dcbf6, expected_exit_code=86. Require terminal FAILED with RuntimeCudaOomError, receipt terminal_status=CUDA_OOM/cuda_oom=true/automatic_retry_eligible=false, matched trusted-probe evidence with systemd Result=exit-code ExecMainCode=1 ExecMainStatus=86, exactly the accepted A4500 visible, other GPU denied, zero project/GPU process residue, runner/staging removed, expanded-runtime pre/post digest identical to b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63, JIT/credential absent, gpu-small live lane unquarantined, and no model weights/inference. After PASS, checkpoint CUDA OOM acceptance and proceed to CPU/GPU contention/concurrency proof, then cache poisoning/incomplete snapshot rejection.

## Remaining work

- Run one bounded root-authored gpu-small CUDA OOM host canary using only the installed trusted CUDA OOM probe on accepted GPU UUID GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea. No GitHub job, candidate payload code, model weights, or inference.
- After CUDA OOM PASS, checkpoint the failure envelope and run CPU/GPU contention and concurrency acceptance without expanding gpu-small authority.
- Run cache poisoning and incomplete-snapshot rejection acceptance against the trusted-cache boundary.
- After the adversarial recovery/resource/cache matrix is complete, run the first offline Qwen3.5-4B pinned-model pilot on gpu-small under the already-promoted model/runtime identities.
- Decide separately whether gpu-heavy or dual-GPU should ever be accepted; they remain denied.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-lambda-execution-policy-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
