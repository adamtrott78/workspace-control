<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: `tasks/active/workspace-lambda-execution-policy-v1.json`

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: `workspace-lambda-execution-policy-v1`
- Status: `IN_PROGRESS`
- Owning stage: `adversarial_recovery_and_resource_validation`
- Current workspace-control implementation checkpoint before this handoff branch: `effc5b2f39fe897f4b9dc9fe6767d2002ee81cdb`
- Research-engine accepted gpu-small candidate/run evidence remains unchanged; do not rerun accepted gates merely for measurement.

## Accepted adversarial matrix so far

- **Immutable expanded-runtime adversarial path implementation and trusted workflow: PASS**
- **First live adversarial gpu-small admission fail-closed on verifier format mismatch: PASS**
- **Live immutable-runtime adversarial gpu-small execution: PASS**
- **Controller/provisioner restart and terminal replay recovery: PASS**
- **Cleanup-failure lane quarantine implementation: PASS**
- **Kill-switch hard-disable and epoch revocation: PASS**
- **CPU timeout failure envelope: PASS**
- **CPU/RAM resource-exhaustion failure envelope: PASS**
- **Disk-pressure failure envelope: PASS**
- **Trusted CUDA OOM acceptance-probe implementation: PASS**

## Resource-failure envelope status

- Timeout: PASS — real transient unit -> `TIMED_OUT`, no retry, cleanup complete.
- CPU/RAM OOM: PASS — root-owned systemd `Result=oom-kill` -> `CPU_OR_RAM_RESOURCE_EXHAUSTED`, no retry, cleanup complete.
- Disk pressure: PASS — bounded 32 MiB tmpfs genuine ENOSPC plus root `statvfs` zero-available-block evidence -> `DISK_PRESSURE`, no retry, cleanup complete; tmpfs unmounted cleanly.
- CUDA OOM: implementation/hardening PASS; live bounded host canary PENDING.

## CUDA OOM trust boundary

Arbitrary CUDA allocation failures are application-level failures. There is no trustworthy systemd/NVML terminal flag analogous to cgroup `oom-kill`, so candidate stdout/stderr or arbitrary exit codes MUST NOT classify `CUDA_OOM`.

Accepted implementation:
- PR #176 head `d2aec63a8f87695714563ccf6d61f5cf03e44879`
- Workspace Control Validation run `37870670623`: SUCCESS
- Squash merge/main: `effc5b2f39fe897f4b9dc9fe6767d2002ee81cdb`
- Runtime blob: `4615bcb7a06253186b61d31688f7720b45e760f0`
- Trusted probe source: `scripts/lambda_ci_cuda_oom_probe.py`
- Trusted probe blob: `046f614508dd6b5f7cab981fc803a20ea33dcbf6`
- Bootstrap blob: `78b2320b4ccc69161b8e9538c4eb33b291a20c52`
- Installed probe path: `/opt/workspace-ci/provisioner/trusted-probes/lambda_ci_cuda_oom_probe.py`
- Installed probe must be root-owned, regular, and non-writable; bootstrap installs mode 0555.
- Trusted binding: `kind=cuda_oom_acceptance_v1`, `authority=ROOT_SYNTHETIC_CANARY_ONLY`, exact path/blob, expected exit `86`.
- Normal admitted launch specs omit `trusted_failure_probe`; request validation rejects candidate-supplied `trusted_failure_probe`.
- Trusted probe runs with the accepted expanded-runtime Python and is read-only bound into the gpu-small sandbox. It replaces candidate command execution for the synthetic acceptance canary.
- Probe reads/clears one opaque stdin line, selects CUDA device 0 inside the already one-GPU namespace, gets free VRAM, requests `free + 256 MiB`, and exits 86 only on an actual CUDA OOM observed inside the trusted probe. Unexpected success=87; unexpected error=88.
- Root classification requires verified probe binding AND root-owned systemd `Result=exit-code`, `ExecMainCode=1`, `ExecMainStatus=86`.
- Candidate output text is never part of CUDA-OOM classification.

## Immutable runtime / GPU invariants that remain binding

- Accepted GPU UUID: `GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea` only.
- gpu-heavy / dual-GPU remains denied.
- Expanded runtime manifest: `f67ff9a26690c55930232c915e59e826e3cca2dd89012de9e35a852032b38f74`
- Expanded runtime tree digest: `b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63`
- Runtime ID: `qwen35-vllm-cu129-image-native-sampler-v3`
- No model weights or inference are authorized for the CUDA-OOM canary.
- Cleanup failure, GPU-process leak, model-server leak, or runtime post-verification failure must quarantine the lane; ordinary payload/resource failure with successful cleanup must not.

## Exact next safe action

Install exact workspace-control SHA effc5b2f39fe897f4b9dc9fe6767d2002ee81cdb on the Lambda host using the existing authorized P5 bootstrap and verify runtime blob 4615bcb7a06253186b61d31688f7720b45e760f0 plus installed trusted CUDA OOM probe blob 046f614508dd6b5f7cab981fc803a20ea33dcbf6 at /opt/workspace-ci/provisioner/trusted-probes/lambda_ci_cuda_oom_probe.py, root-owned and non-writable. Then run one root-authored synthetic gpu-small CUDA OOM host canary only on accepted GPU UUID GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea. Do not submit a GitHub job; do not use candidate payload code; do not load model weights or perform inference. The synthetic launch spec may add trusted_failure_probe only after ordinary validated gpu-small spec construction, with kind=cuda_oom_acceptance_v1, authority=ROOT_SYNTHETIC_CANARY_ONLY, exact installed path, source_blob_sha=046f614508dd6b5f7cab981fc803a20ea33dcbf6, expected_exit_code=86. Require terminal FAILED with RuntimeCudaOomError, receipt terminal_status=CUDA_OOM/cuda_oom=true/automatic_retry_eligible=false, matched trusted-probe evidence with systemd Result=exit-code ExecMainCode=1 ExecMainStatus=86, exactly the accepted A4500 visible, other GPU denied, zero project/GPU process residue, runner/staging removed, expanded-runtime pre/post digest identical to b0cbb4efbe8673bdb421bad8036d29864bffe0687a9a654bbd95f54544659e63, JIT/credential absent, gpu-small live lane unquarantined, and no model weights/inference. After PASS, checkpoint CUDA OOM acceptance and proceed to CPU/GPU contention/concurrency proof, then cache poisoning/incomplete snapshot rejection.

## Remaining adversarial work after CUDA OOM

1. CPU/GPU contention and concurrency proof.
2. Cache poisoning / incomplete trusted snapshot rejection proof.
3. Only after the entire adversarial matrix is accepted: first offline pinned Qwen3.5-4B gpu-small pilot; gpu-heavy/dual-GPU remains a separate future decision.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:

`tasks/active/workspace-lambda-execution-policy-v1.json`

Start from the normal `workspace-control` root route.

Treat the authoritative task capsule, its synchronized Markdown handoff, exact durable Git/runtime state, and referenced evidence as the complete handoff. Do not rely on previous conversation state or another chat's prose summary.

Use the connected Workspace Heartbeat plugin according to `procedures/progress_heartbeat.md`.

Do not change task ownership, scope, or `next_safe_action` merely because this is a new chat.
