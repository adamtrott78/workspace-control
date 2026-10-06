# Lambda CI Workload Policy v1

Status: **contract candidate; not wired into the live Lambda**

Owning task: `workspace-lambda-execution-policy-v1`

Machine-readable authority:
`architecture/lambda-ci-workload-policy.v1.json`

Schemas:

- `schemas/lambda-ci-workload-policy.v1.schema.json`
- `schemas/lambda-ci-admission-manifest.v1.schema.json`
- `schemas/lambda-ci-execution-receipt.v1.schema.json`

## 1. Boundary and non-goals

This contract sits above the already accepted P5 execution substrate. It does not
re-prove or widen that substrate.

Accepted substrate capabilities remain:

- `cpu-test` on `lambda-research-engine`;
- `gpu-small` on `lambda-research-engine-gpu`;
- single-job JIT runners;
- unprivileged GitHub-facing controller;
- credential-blind root provisioner;
- project UID isolation;
- private/local/production-service denial;
- candidate workspace teardown and CPU/GPU cleanup;
- the single accepted RTX A4500 UUID
  `GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea`.

The static `gpu-heavy` profile is **not** authority. This policy denies the
`gpu-heavy` workload class until a later explicit acceptance decision.

This contract does not authorize live Lambda mutation, production daemon
execution, scientific-state mutation, sustained model servers, or dual-GPU work.

## 2. Core authority rule

A workflow, ChatGPT action, candidate commit, or request payload may **request**
a declared workload class. It never grants one.

The root-owned policy object is authority. A root-issued admission manifest is
the only per-execution grant.

Therefore:

1. candidate/request fields are claims;
2. root policy validates project, trusted workflow, candidate SHA, workload
   class, profile, model/runtime/cache identities, resource ceilings and
   capability classes;
3. root emits an immutable bounded admission manifest;
4. the admission is single-use and short-lived;
5. execution must produce a receipt bound back to that exact admission.

Unknown workload classes, mismatched bindings, stale policy/profile/cache
identity, revoked exceptions, and replay conflicts fail closed.

## 3. Workload taxonomy

| Workload | Plane | Candidate payload | Profile/envelope | Network | Persistent cache | State effects | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `cpu-test` | JIT runner | yes | `cpu-test` | accepted public payload egress; private/local denied | none | CI validation only | existing P5 capability |
| `gpu-small` | JIT runner | yes | `gpu-small` | accepted public payload egress; private/local denied | none | CI validation only | existing P5 capability |
| `model-acquire` | trusted acquisition | no | `cpu-test` envelope | declared public artifact source only | quarantine only | quarantine artifacts only | designed, not live |
| `cache-promote` | trusted cache manager | no | bounded CPU envelope | none | trusted promotion only | trusted cache promotion only | designed, not live |
| `model-eval-single-gpu` | JIT runner | yes | `gpu-small` | runner control plane only; payload offline | promoted model/runtime read-only | non-scientific eval only | designed, not live |
| `gpu-heavy` | none | no | underlying static profile exists | n/a | n/a | n/a | **DENY** |

A workload class is not an alias for a runner profile. It is the conjunction of:

- execution plane;
- project/repository binding;
- exact trusted workflow identity;
- exact candidate SHA;
- resource class;
- payload network class;
- payload secret class;
- filesystem class;
- cache-access class;
- state-effect class;
- model/runtime/cache identity requirements;
- exception set;
- receipt requirements.

## 4. Model, runtime and cache identity

Model weights and executable runtime dependencies are distinct identities.

A model-eval admission must bind:

- upstream model repository;
- exact immutable revision/commit;
- promoted cache object ID;
- complete content/tree SHA-256 identity;
- complete manifest SHA-256;
- promotion receipt SHA-256;
- serialization-risk class;
- offline-completeness result.

A runtime admission must independently bind:

- runtime contract ID;
- promoted runtime cache object ID;
- runtime tree SHA-256;
- dependency-manifest SHA-256;
- promotion receipt SHA-256;
- exact owning research-engine contracts and Git commit.

Mutable branch names such as `main` are never durable promoted identities.
Resolve-once acquisition is permitted only when the resolved immutable revision
is recorded before promotion.

A model-eval job must fail before model initialization when a required promoted
object is missing, incomplete, digest-mismatched, stale relative to policy, or
not reopenable locally.

Candidate jobs never write the trusted cache.

## 5. Network and secrets

### Existing CPU/GPU compatibility mode

The already accepted `cpu-test` and `gpu-small` capabilities retain their
existing public-egress behavior while private/local/production services remain
denied.

### Model evaluation

`model-eval-single-gpu` is payload-offline by default.

The JIT runner may require GitHub control-plane connectivity, but the model
payload must not gain general public/model-registry egress. Implementations
therefore need a boundary between runner control traffic and payload traffic;
"the runner needs GitHub" is not permission to give the model process Internet
access.

No model-registry credential may enter the candidate/model payload.

### Acquisition

`model-acquire` has no candidate payload. Network access belongs to a trusted
fetcher and is limited to the declared public artifact source plus unavoidable
public CDN redirects. Private/local/production ranges remain denied.

An optional registry credential may be visible only to that trusted fetcher and
must never be:

- written into model/runtime cache content;
- written into task capsules or receipts;
- inherited by candidate code;
- persisted after the operation.

### Promotion

`cache-promote` is offline.

## 6. Filesystem and cache classes

Candidate execution gets only bounded per-admission writable state:

- job workspace;
- ephemeral home/scratch explicitly granted by the admission.

Candidate-writable package/model caches must not persist across jobs.

Trusted acquisition writes to a unique admission-owned quarantine object.
Quarantine is not trusted cache and is not consumable by model-eval.

Trusted promotion is a separate operation using a trusted identity unavailable
to candidate code. Promotion verifies provenance/risk metadata and atomically
creates an immutable trusted-cache object.

Model evaluation mounts only the exact promoted model/runtime objects read-only.

No admission grants access to personal home, controller credentials, Docker
sockets, SSH keys, browser credentials, production PostgreSQL, or research-engine
production/scientific state.

## 7. Unsafe serialization and custom executable code

Default posture is fail closed.

Safe serialization is the ordinary path. Safetensors and inert JSON/text/tokenizer
assets are expected examples.

The following require an explicit separately reviewed exception:

- pickle-backed checkpoints/deserializers;
- arbitrary PyTorch pickle checkpoints;
- `trust_remote_code` or equivalent remote/custom Python code;
- mixed or unknown executable model material.

An exception is not a boolean supplied by a workflow. It is a root-owned policy
record bound to the exact project, model revision, model cache digest, runtime
cache digest, executable dependency digest, allowed entrypoint/deserializer,
reviewer, and validity interval.

Changing any bound identity invalidates the exception.

Policy v1 contains **zero approved unsafe-serialization/custom-code exceptions**.

## 8. Admission freshness and replay

Each root-issued admission is:

- bound to one request ID and canonical request digest;
- bound to one policy ID/epoch/digest;
- bound to one project-profile digest and kill-switch epoch;
- bound to one exact trusted workflow blob/default-branch commit;
- bound to one exact candidate SHA;
- short-lived;
- single-use.

Required replay behavior:

- same request ID + different request digest -> reject;
- same request ID + identical digest and still unconsumed -> return the same
  admission, never mint a second grant;
- same consumed request with a terminal receipt -> return the existing receipt,
  never silently reexecute;
- consumed request with no trustworthy terminal receipt after restart -> mark
  indeterminate/recover cleanup and require a fresh request for execution;
- expired admission -> reject and require a fresh request.

Outstanding admissions become stale when policy epoch/digest, project profile,
required cache identity, required exception state, or kill-switch generation
changes.

The admission must be atomically consumed before runner/payload launch.

## 9. Resource policy

The admission binds ceilings, not targets.

The policy currently constrains:

- wall-clock runtime;
- scratch bytes;
- staging bytes;
- GPU count/UUIDs.

The underlying accepted P5 profiles remain authoritative for CPU quota, RAM,
TasksMax, GPU-device exposure and cgroup kill behavior. Admission enforcement
must never grant a ceiling above the selected underlying profile.

Before the new workload classes become live, enforcement must also establish:

- bounded disk accounting/quota or an equivalently fail-closed hard limit;
- peak RSS and process/task evidence;
- peak scratch/staging evidence;
- peak VRAM evidence for GPU/model jobs.

The first model-eval class remains single-GPU and binds only
`GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea`.

## 10. Failure and cleanup semantics

Payload failure is not permission to retry automatically.

Timeout, CPU/RAM exhaustion, CUDA OOM, disk pressure, kill-switch termination,
and cancellation all produce terminal receipts and mandatory cleanup.

Cleanup is part of job correctness, not best-effort housekeeping.

Every terminal path checks at minimum:

- cgroup empty;
- zero project-UID processes;
- zero GPU compute processes;
- zero model servers;
- job workspace removed;
- ephemeral staging removed;
- JIT configuration absent;
- GitHub credential residue absent.

A cleanup failure, leaked GPU process, or leaked model server quarantines the lane
and blocks new admissions until trusted recovery proves the lane clean.

A controller restart may recover state, but it must not blindly replay a consumed
admission.

## 11. Concurrency and locks

Admission enforcement must acquire the resources it grants.

At minimum:

- a physical GPU UUID is exclusive to one admitted GPU/model payload at a time;
- a quarantine/promotion object is exclusively mutated by one trusted operation;
- trusted cache objects may be shared read-only only after complete promotion;
- CPU and GPU lanes may run concurrently only within their independently accepted
  resource boundaries;
- `gpu-heavy` may not be synthesized from two simultaneous single-GPU grants.

Backpressure is a failure/deferral result, not authority to widen resources.

## 12. Execution receipt

Every admitted execution produces a non-secret receipt conforming to
`lambda-ci-execution-receipt-v1`.

The receipt binds:

- policy and admission identity;
- project;
- trusted workflow and candidate SHA;
- workload/resource profile;
- exact model/runtime/cache objects;
- runner/JIT identity;
- actual GPU UUID(s), driver and CUDA runtime when applicable;
- resource peaks;
- network class evidence;
- state-effect evidence;
- terminal status/exit code;
- cleanup result;
- hashed evidence locations.

A successful payload with failed cleanup is **not** a successful job.

## 13. First model pilot

The only first-model candidate in policy v1 is:

- model: `Qwen/Qwen3.5-4B`;
- exact revision: `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`;
- runtime contract:
  `qwen35-vllm-cu129-image-native-sampler-v3`.

The model/runtime scientific and runtime truth remains owned by research-engine,
including:

- `benchmarks/document_intelligence/residual-model-prefetch-contract.v1.json`;
- `benchmarks/document_intelligence/qwen35-runtime-certification-contract.v1.json`;
- `benchmarks/document_intelligence/local-inference-service-contract.v1.json`;
- `benchmarks/document_intelligence/qwen35-guarded-semantic-calibration-contract.v1.json`.

Workspace-control references those exact owning contracts; it does not copy their
scientific semantics.

Before the pilot can run:

1. admission enforcement must be accepted;
2. model/runtime content must be promoted through trusted cache tooling;
3. promoted objects must pass offline completeness/digest validation;
4. the admission must select `model-eval-single-gpu`;
5. the payload must be offline and credential-free;
6. the first workload is the existing synthetic non-scientific image+text canary,
   not a scientific benchmark;
7. no production routing or scientific state changes;
8. cleanup must prove zero persistent model-server/process residue.

Passing this pilot does not enable `gpu-heavy`.

## 14. Stage gate

This document and its machine-readable contracts are policy design only.

The next stage, `admission_manifest_and_enforcement`, may begin only after:

- the policy JSON and schemas parse;
- adversarial contract tests pass;
- workspace-control FULL_INTEGRATION validation passes;
- the contract is merged to canonical main;
- the durable task capsule is advanced atomically with its derived Markdown
  handoff.

No live Lambda mutation is part of this contract stage.
