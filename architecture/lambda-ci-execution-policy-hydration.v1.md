# Lambda Execution Policy v1 — Hydration and Source Map

Status: bootstrap context for `workspace-lambda-execution-policy-v1`

## Purpose

This document front-loads the durable context needed to design Lambda workload
admission, trusted model/dependency caches, resource governance, and model-scale
execution policy without rediscovering the accepted P5 substrate or duplicating
research-engine scientific/model truth.

The parent execution substrate is already accepted. This child task begins at
the policy boundary.

## Accepted execution baseline

Workspace-control canonical baseline:

`12f9d9e3a59f042bcf832dfe89a3b389b92f21ce`

Research-engine canonical baseline:

`577764f4db10e4f4f894b1613518c358c6da7b95`

The accepted live Lambda install is rooted in workspace-control
`ebfbae64dc82afaf81123ba49b03d170a0196757`.

### CPU lane

- scale set: `lambda-research-engine`
- profile: `cpu-test`
- project UID: `ci-research-engine`
- one-job JIT runner semantics
- candidate SHA verified by trusted default-branch workflow
- personal home, controller credential, Docker, production PostgreSQL, and GPU
  access denied
- candidate workspaces destroyed post-job
- no JIT or GitHub credential persistence

Accepted sequential runs:

- GitHub run `37422040174`, artifact `11397464532`
- GitHub run `37433722972`, artifact `11397719082`

### GPU lane

- scale set: `lambda-research-engine-gpu`
- profile: `gpu-small`
- exact target UUID:
  `GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea`
- target device at acceptance: `/dev/nvidia1`
- non-selected GPU denial target: `/dev/nvidia0`
- shared compute support nodes: `/dev/nvidiactl`, `/dev/nvidia-uvm`,
  `/dev/nvidia-uvm-tools`
- runner device boundary remains `DevicePolicy=closed`
- production/scientific state remains denied

Accepted sequential runs:

- GitHub run `37512259673`, artifact `11437401396`,
  runner `lambda-research-engine-gpu-b8aec734f582`
- GitHub run `37515305255`, artifact `11435883779`,
  runner `lambda-research-engine-gpu-a0e44f66d7b5`

Both runs:

- saw exactly one CUDA-visible RTX A4500;
- matched the exact target UUID;
- denied `/dev/nvidia0` with EPERM;
- created a CUDA context;
- allocated and freed 268,435,456 bytes;
- returned free VRAM exactly to the pre-allocation value;
- left no project or GPU compute processes.

Accepted local cleanup receipts:

- `/srv/workspace-ci/research-engine/logs/p5-3e8bf4ec-479c-47e2-b3fc-cdb7fed22962-receipt.json`
- `/srv/workspace-ci/research-engine/logs/p5-6605c134-6bad-4b96-a809-1b52e6889c32-receipt.json`

Both report `RUNNER_EXITED_CLEANLY`, exit 0, no GitHub credential/JIT
persistence, CPU/GPU process cleanup true, and job/staging workspace destruction.

## Existing workspace-control policy primitives

### Trusted-cache split

Authoritative design:
`architecture/lambda-ci-trusted-cache-policy.v1.md`

Roots for research-engine:

- candidate-writable staging:
  `/srv/workspace-ci/research-engine/staging-cache`
- runner-read-only trusted cache:
  `/srv/workspace-ci/research-engine/trusted-cache`

Candidate jobs must not promote directly.

Existing promotion requirements already include:

1. artifact kind;
2. immutable upstream identity;
3. SHA-256 or stronger source/archive digest;
4. source repository/model identifier;
5. license/usage review;
6. extraction/build recipe identity;
7. resulting tree/content digest;
8. malware/custom-code risk classification;
9. promotion receipt.

This is the correct primitive to promote into the workload-admission plane rather
than replacing it.

### Current project/profile manifest

Authoritative source:
`architecture/lambda-ci-project-research-engine.v1.json`

Current profiles:

- `cpu-test`: 800% CPU, 32 GiB max RAM, 30 min, no GPU
- `gpu-small`: 1200% CPU, 64 GiB max RAM, 20 min, one exact GPU UUID
- `gpu-heavy`: 2400% CPU, 192 GiB max RAM, 4 h, both GPUs, explicitly
  unauthorized pending separate acceptance

Current public egress is allowed for accepted profiles while private/local host
ranges and production PostgreSQL are denied. Policy design should decide whether
model-eval becomes offline/no-egress and acquisition becomes the only model
network path.

### Current provisioner authority

The root provisioner has no GitHub credential. It accepts only manifest-derived
project/profile/JIT launch requests from the unprivileged controller over the
local Unix socket.

The next policy layer must preserve this rule:

> ChatGPT/workflow code may request a declared capability; only root-owned policy
> may grant it.

Candidate-controlled workflow input must never directly widen device, filesystem,
network, secret, cache-promotion, production-state, or runtime authority.

## Existing research-engine model/runtime governance

Research-engine remains authoritative for model-specific scientific/runtime
truth. Workspace-control should consume exact identities and required execution
properties without copying scientific decisions.

### Qwen3.5-4B

Current accepted identity:

- model: `Qwen/Qwen3.5-4B`
- exact revision:
  `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`
- existing model store:
  `~/.research-engine/residual-models/qwen3.5-4b/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`
- runtime:
  `~/.research-engine/residual-runtimes/qwen3.5-4b-vllm-0.30.0`
- runtime contract:
  `qwen35-vllm-cu129-image-native-sampler-v3`
- current production use: bounded page-scoped VERIFY
- current VERIFY GPU index: 1
- whole-job fallback: fail closed to STANDARD Codex if any local page unit is
  ineligible, partial, negative, backpressured, runtime-failed, or issue-bearing

Relevant contracts:

- `benchmarks/document_intelligence/qwen35-runtime-certification-contract.v1.json`
- `benchmarks/document_intelligence/local-inference-service-contract.v1.json`
- `benchmarks/document_intelligence/qwen35-guarded-semantic-calibration-contract.v1.json`
- `benchmarks/document_intelligence/qwen35-grounded-extract-contract.v1.json`

### Existing residual-model prefetch gate

Authoritative source:
`benchmarks/document_intelligence/residual-model-prefetch-contract.v1.json`

Existing useful controls:

- dedicated local model root;
- exact revision resolution/pinning;
- Apache-2.0 metadata verification;
- complete sorted per-file SHA-256 manifests;
- disk-space preflight;
- per-artifact size ceilings;
- local-files-only reopen verification;
- zero inference during prefetch;
- daemon remains stopped;
- no scientific-state materialization;
- package-wheel SHA pinning.

Known candidate identities include:

- Qwen3.5-4B:
  `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`
- PaddleOCR-VL-1.6:
  `c5630abae1d940eafe0697512a0325494b02ab42`
- CodeFormulaV2:
  `0284bc97b73c88776957d00d6695dd63a5a8784e`
- PP-OCRv6 detection/recognition currently use resolve-once main semantics and
  therefore should become exact revisions before trusted-cache promotion.

### Local inference owner semantics

Research-engine already implements:

- one long-lived owner process per heavyweight model family;
- bounded FIFO queue per family;
- immediate backpressure failure when queue is full;
- serialized execution within a family;
- no duplicate model instance per family;
- explicit family switching/eviction on a shared GPU;
- explicit close/cleanup lifecycle.

Current production local-inference defaults:

- max pending: 8
- timeout: 900 s
- formula GPU: 0
- table GPU: 1
- Qwen VERIFY GPU: 1
- table and Qwen VERIFY are mutually exclusive residents on GPU 1
- formula may execute concurrently on GPU 0

The CI policy should reuse these semantics when a model workload requires a
resident model but must not accidentally create a sustained production daemon.

## Policy gaps that remain

The accepted execution substrate deliberately does not yet define all of the
following:

1. a first-class workload/admission manifest distinct from a project/profile;
2. model identity as an admission input;
3. dependency-lock/environment identity as an admission input;
4. acquisition vs promotion vs evaluation capability separation;
5. a candidate-inaccessible model registry token path;
6. offline/no-egress model-eval class;
7. custom-code / pickle / unsafe-serialization default-deny rules;
8. durable trusted-cache promotion tooling and receipts;
9. cache invalidation/eviction enforcement;
10. model/runtime tree digest verification immediately before execution;
11. disk/scratch ceilings and disk-pressure failure semantics;
12. resource-peak telemetry in standard CI receipts;
13. replay/restart/cleanup-failure/kill-switch adversarial acceptance;
14. dual-GPU/gpu-heavy admission and scheduling;
15. model-server lifetime policy for CI;
16. cross-project cache reuse policy;
17. second-project policy isolation.

These gaps are the owning scope of the child task.

## External primary-source guidance hydrated on 2026-10-06

### GitHub Actions

Current GitHub documentation reinforces:

- self-hosted runners do not inherently provide clean ephemeral VMs;
- untrusted workflow code can persist compromise on reusable self-hosted hosts;
- private/repository-scoped access is preferred;
- JIT runners are single-job and automatically removed if unused;
- scale-set/autoscaling clients are appropriate for higher-volume custom
  autoscaling;
- workflow/repository credentials should remain narrowly scoped.

This supports retaining one-job JIT runners and treating policy admission as a
privileged control-plane decision rather than a workflow convention.

### Hugging Face

Current Hugging Face documentation reinforces:

- `snapshot_download(..., revision=<commit>)` provides commit-addressed model
  snapshots;
- `local_files_only=True` can fail closed with an incomplete-snapshot error
  instead of silently returning a partial snapshot;
- cache paths are configurable and content is reused across revisions;
- pickle checkpoints can execute arbitrary code during deserialization;
- safetensors/safe serialization is recommended for security;
- unsafe/custom executable model code must be treated as executable dependency
  material, not as inert weights.

These semantics map directly to the existing candidate-staging/trusted-cache
split.

## Recommended policy architecture

The child task should design and then enforce these workload classes:

1. `cpu-test`
   - existing accepted profile;
   - ordinary deterministic/unit/integration validation;
   - no GPU/model authority.

2. `gpu-small`
   - existing accepted one-A4500 profile;
   - hardware-aware tests and bounded CUDA work;
   - no implicit model/cache authority.

3. `model-acquire`
   - network-enabled trusted operation;
   - exact model revision required;
   - optional registry credential isolated from candidate code;
   - downloads only into quarantine/staging;
   - no scientific/model inference.

4. `cache-promote`
   - separate trusted identity;
   - validates source/revision/digests/license/serialization/custom-code risk;
   - atomically promotes immutable content-addressed objects;
   - writes a durable promotion receipt;
   - candidate workflows cannot invoke directly.

5. `model-eval-single-gpu`
   - consumes only promoted read-only model/runtime objects;
   - offline/local-files-only by default;
   - one accepted GPU UUID;
   - no registry credential;
   - no production/scientific-state mutation;
   - mandatory execution and cleanup receipt.

6. `gpu-heavy`
   - deferred;
   - both GPUs / longer runtime;
   - requires explicit acceptance after the policy/adversarial gates pass.

Production daemon/scientific-state mutation remains outside CI and requires a
separate production-operation contract.

## Admission record

A workload admission request should ultimately bind at least:

- project/repository;
- trusted default-branch workflow identity;
- exact candidate SHA;
- workload class/profile;
- model repo + exact revision + trusted-cache object/tree digest when applicable;
- runtime/dependency lock identity;
- CPU/RAM/GPU/time/disk class;
- egress class;
- secrets class;
- filesystem/state-effect class;
- cache access class;
- expected evidence/receipt schema;
- explicit exception flags, if any.

The root-owned policy object is authority. Workflow/request fields are claims to
validate against that authority.

## First pilot after policy acceptance

Use the already-certified Qwen3.5-4B revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`.

The first pilot should:

1. promote the exact existing model snapshot/runtime identity into the new
   trusted-cache model rather than redownload blindly;
2. verify hashes, license, serialization/custom-code posture, and completeness;
3. execute a non-scientific bounded canary/benchmark using
   `model-eval-single-gpu`;
4. prove offline/local-files-only execution;
5. record model/runtime/workflow/candidate/hardware identities;
6. prove cleanup and zero persistent model-server/process state;
7. only then permit research-engine-specific model benchmark use.

Do not enable `gpu-heavy` merely because this pilot passes.

## Heartbeat cross-chat rule

Heartbeat mount state is chat-surface-local and must never be persisted as if it
were task-global.

Every fresh ChatGPT chat/surface doing substantial work must:

1. emit one initial `heartbeat_update`;
2. call `heartbeat_open(task_id)` exactly once early in that chat;
3. use data-only updates afterward while the card is healthy;
4. use one recovery open only if the card is demonstrably lost/failed.

A handoff may persist the task ID, but never the claim that the card is already
mounted in the receiving chat.
