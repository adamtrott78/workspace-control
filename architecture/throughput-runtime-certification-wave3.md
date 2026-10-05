# Throughput Efficiency Wave 3 — Execution Certification and Control-Cycle Economy

Status: **implemented v1; field validation active**

## Shared implementation

Wave-3 shared control-plane primitives are implemented on workspace-control
main at commit `54758e227ed452ac0d7598889158ddd04e254a4c` (PR #56,
FULL_INTEGRATION run 37257188954 PASS).

Implemented surfaces:

- `scripts/runtime_certification.py`: canonical execution/operation identities,
  C0-C4 stage validation, typed certification invalidation, R0-R3 reuse state,
  idempotent recovery decisions, and structured process matching;
- `schemas/runtime_certification.v1.schema.json`;
- `schemas/runtime_operation_receipt.v1.schema.json`;
- `schemas/runtime_failure_envelope.v1.schema.json`;
- `tests/test_runtime_certification.py`: 16 focused regression tests.

Implementation does not move project-specific model/backend/scientific truth into
workspace-control. Field validation remains active for verified R2 compile/JIT
cache reuse and the first real owning-project C3 same-modality canary.

## Purpose

Wave 3 converts the runtime and orchestration lessons from Wave 2 into a
repository-neutral certification and recovery architecture.

Wave 2 proved that cheap host/build checks, exact package identity, import/native
smoke tests, compact receipts, and deterministic artifact caches remove real
waste. It also exposed their boundary: an environment can pass exact imports and
a real CUDA allocation while the actual engine later fails during model/runtime
initialization. The Qwen3.5 field workload demonstrated this directly: package
identity and import/CUDA smoke passed, the engine loaded an 8.68 GiB checkpoint
and performed substantial compile/profile/warmup work, then an optional
FlashInfer sampling backend attempted JIT compilation and failed because its
selected execution plan required an unavailable CUDA compiler/toolkit. No model
inference call began.

Wave 3 therefore stops asking only whether an environment is *probably
compatible*. It asks whether the exact execution capability required by the
workload has been demonstrated, recorded, and can be reused safely.

This document defines shared mechanism only. Qwen, vLLM, FlashInfer, package
versions, model revisions, prompts, scientific thresholds, and project-specific
cache keys remain owning-project truth.

## Design goals

1. discover as many compatibility defects as possible before expensive work;
2. distinguish package/native compatibility from dynamic backend/toolchain
   compatibility and real engine viability;
3. require actual engine boot plus one bounded same-modality synthetic canary
   before writing a reusable runtime-ready certification;
4. aggregate independently detectable defects rather than fixing one failure per
   control cycle;
5. persist reusable compile/runtime caches under complete compatibility identity;
6. make every long operation resumable from durable stage receipts;
7. preserve child-process/JIT root causes in compact machine-readable failure
   envelopes;
8. replace textual process resemblance with structured process identity;
9. stop diagnosis once a bounded safe corrective action is established;
10. measure assistant/orchestration wall time as a first-class latency component;
11. preserve scientific, repository, provenance, daemon, production-routing, and
    mutation-authority boundaries.

## Certification ladder

The certification ladder is monotonic. A later stage may depend on all earlier
stages, but passing an early stage MUST NOT be described as proof of a later one.

### C0 — static environment and dependency closure

C0 inventories and validates facts that can be established without starting the
heavy engine.

At minimum, where applicable:

- Python ABI and package/lock/wheel identity;
- wheel and model/config hashes needed for execution identity;
- accelerator architecture and driver/runtime compatibility predicates;
- native shared-library dependencies of selected extensions;
- required external executables, compilers, build tools, headers, and runtime
  services implied by the selected execution plan;
- project runtime-contract version.

C0 SHOULD aggregate independent failures into one report. For example, multiple
missing shared libraries, incompatible package builds, and missing toolchain
executables should be returned together when they can be detected independently.

A static scanner cannot discover every conditional runtime dependency. C0 is
therefore necessary evidence, not a runtime-ready claim.

### C1 — exact import and accelerator certification

C1 executes the narrow, real library path used by the workload and proves:

- exact expected package identity still holds;
- required imports/native modules resolve;
- the accelerator is visible;
- one bounded real accelerator allocation succeeds;
- no unexpected environment mutation occurred.

C1 is intentionally cheap. It catches package/native failures before model load,
but it MUST NOT be labelled full execution-path certification.

### C2a — execution-plan and backend/toolchain certification

Before expensive engine boot, resolve the runtime choices that can introduce
conditional dependencies.

Examples of the *kind* of facts to resolve, when relevant:

- sampling backend;
- attention/backend implementation;
- compiler/JIT path;
- distributed/executor backend;
- image/audio/video processor backend;
- kernel/provider/plugin selection.

Record an execution-backend manifest. Validate the requirements introduced by
the selected plan: binaries, compilers, headers, shared libraries, cache
locations, services, IPC facilities, or compatibility predicates.

If a compatible supported backend avoids an unnecessary optional dependency,
selecting it is allowed only when the owning project establishes semantic
equivalence for its workload contract. The backend choice then becomes part of
execution identity; it must not be a silent fallback.

The FlashInfer/nvcc field failure is the motivating example: package/import/CUDA
checks passed, but the dynamically selected sampler introduced a JIT compiler
requirement that was not represented in earlier certification.

### C2b — real engine-boot certification

Instantiate the exact engine/model configuration required by the workload and
wait for a healthy initialized state.

This stage is expected to exercise expensive boundaries that C1 cannot:

- worker/core subprocess startup;
- IPC/shared memory;
- model/config/tokenizer/processor loading;
- model weights;
- scheduler/executor initialization;
- attention/kernel/backend selection;
- compilation/JIT and cache reuse;
- accelerator memory planning and allocation.

A successful import is not a substitute for successful engine initialization.

C2b records boot time, material reusable-cache hits/misses, resource observations,
and structured subprocess outcomes. Partial resource values from a failed boot
remain diagnostic evidence and MUST NOT be presented as a completed workload
benchmark.

### C3 — bounded same-modality synthetic canary

After engine boot, execute one tiny deterministic synthetic request through the
same workload modality and request path.

The canary should minimize cost while exercising the relevant processing chain,
for example:

- deterministic locally generated input;
- tiny prompt/request;
- minimal output budget;
- deterministic sampling where supported;
- no scientific/domain input unless the owning contract explicitly requires it.

C3 proves that request preprocessing, the relevant modality path, scheduling,
model forward execution, accelerator kernels, generation/result production, and
response serialization can complete together.

Only a passing C3 may create the reusable **runtime-certified** sentinel.

### C4 — domain/scientific benchmark

The real benchmark/workflow runs only after required runtime certification is
valid.

C4 owns domain truth: authoritative sources, prompts, scientific thresholds,
quality scoring, production-routing decisions, provenance, and materialization.
Those facts remain project-local and are not generalized into workspace-control.

## Execution identity versus compatibility predicates

Do not collapse all host facts into one cache key.

**Execution identity** represents bytes/configuration whose change can alter
runtime behavior, such as:

- Python ABI where material;
- exact runtime/package/wheel hashes;
- runtime contract version;
- model/config identity when engine certification is model-dependent;
- selected backend choices;
- engine configuration that affects generated/compiled runtime state;
- certification implementation version.

**Compatibility predicates** describe host conditions under which that identity
remains valid, such as:

- supported driver/API family;
- accelerator architecture or capability;
- available memory floor;
- required external toolchain capability.

A harmless host patch update should not invalidate reusable state merely because
a string changed, but compatibility must be proved rather than assumed.

## Runtime certification bundle

A heavy runtime SHOULD leave a durable bundle with stage-local evidence, for
example:

```text
runtime-certification/
  identity.json
  host.json
  dependency-closure.json
  backend-plan.json
  import-accelerator.json
  engine-boot.json
  synthetic-canary.json
  cache-manifest.json
  certification.json
```

The exact filenames are project-local; the semantic roles are shared.

`certification.json` may claim reusable runtime readiness only if the required
C0-C3 stages pass for the same execution identity and compatible host.

Failures preserve completed earlier stages. A retry resumes from the first
invalid/failed stage instead of repeating all prior work.

## Persistent runtime/JIT cache

Ephemeral benchmark output and reusable compiled runtime state are different
classes of artifact.

Timestamped output roots are appropriate for run evidence. They are poor homes
for compilation/JIT caches that are expensive and deterministic under a stable
execution identity.

Reusable caches SHOULD be stored under a persistent identity derived from all
material compile/runtime inputs and compatibility predicates. Cache reuse must
fail closed on incomplete identity.

The field workload measured roughly 18.28 seconds of compile work plus 48.81
seconds of profiling/warmup before a later engine-startup failure while the cache
was scoped to an ephemeral run directory. This is a high-value natural
measurement target for Wave 3.

## Failure envelopes and child-process evidence

Parent exceptions such as "engine initialization failed" are insufficient when
the causal exception occurred in a child worker, JIT compiler, subprocess, or
service.

Long operations SHOULD preserve a compact failure envelope containing, when
observable:

- operation/stage identity;
- parent exception class/message;
- child role and structured process identity;
- exit status/signal;
- first causal exception class/message;
- concise stderr/traceback excerpt or artifact path;
- complete log artifact reference;
- expensive operations already started/completed;
- scientific/materialization/production state flags.

Full logs remain available, but ordinary diagnosis should begin from the failure
envelope rather than require a large console paste.

## Structured process identity

Process observation MUST use structural identity, not textual resemblance.

Preferred evidence includes:

- owned pidfile or service/unit identity;
- executable identity plus argv positions;
- process group/session/cgroup identity;
- operation receipt with owner PID and start identity.

Flattened substring search such as broad `pgrep -af` over shell wrapper source is
not sufficient. The field workload produced a false active-run detection because
a recovery wrapper contained the future benchmark command in its own `bash -lc`
argument.

## Idempotent staged operations

Each expensive stage SHOULD have a deterministic operation identity derived from
its owning task, source Git state, stage type, execution/runtime identity, and
material inputs.

Before execution, inspect any durable receipt for that operation identity:

- PASS: reuse when still valid;
- RUNNING: inspect structural owner identity before launching another copy;
- FAIL: resume diagnosis/repair from that stage;
- absent/invalid: execute.

This converts interruption recovery from conversational reconstruction into a
bounded durable-state lookup.

## Bounded diagnosis and the actionability gate

Exploratory diagnosis should stop when all of the following hold:

1. the first causal failure is known with sufficient confidence;
2. the corrective action is bounded;
3. repository/scientific/production invariants needed to execute it are known;
4. additional research is not required to make the action safe.

At that point the executor SHOULD checkpoint evidence and execute or return the
next safe action. Additional speculative browsing, broad state reconstruction,
or future-phase design is off the critical path.

New evidence may reopen diagnosis.

## Scope adherence and closure

Wave 3 also bounds implementation scope, not only runtime execution and
diagnosis.

Before substantial multi-step work, derive a compact scope envelope from the
owning task and classify newly discovered work into:

- REQUIRED_CORRECTION: correctness/safety/durability defects that must be fixed;
- BOUNDED_ENABLING_CHANGE: the smallest change that directly unblocks the
  recorded next_safe_action or required validation;
- AUTHORIZED_SCOPE_EXPANSION: adjacent work explicitly authorized by the owning
  scope;
- DEFERRED_FOLLOWUP: useful but non-blocking adjacent work that must be recorded
  rather than implemented now.

The shared implementation is scripts/scope_control.py with
schemas/scope_envelope.v1.schema.json and procedures/scope_closure.md.

A Scope Closure Gate is mandatory once the owning objective is durably satisfied:
if required validation passes, no blocker remains, and no required/bounded/
authorized finding remains, the decision is CHECKPOINT_AND_STOP. Deferred
follow-ups do not keep the current session alive.

This complements the actionability gate: actionability stops unnecessary
diagnosis after a bounded correction is known; scope closure stops unnecessary
implementation after the owning objective is complete.

## Control-cycle latency

Wave 3 measures the end-to-end interval between durable actionable states, not
only CI or program runtime.

Record, where observable:

- assistant/orchestration interval;
- connector reads and writes;
- CI wait;
- human terminal handoff;
- remote runtime/benchmark time;
- recovery/repeated work;
- time from first sufficient root cause to durable corrective mutation;
- number of control cycles per resolved failure.

Operator-observed opaque waits may be recorded as such when exact internal model
timing is unavailable; do not invent precision.

The target is fewer control cycles and less wall time per durable state
transition, not merely faster individual shell commands.

## Git mutation critical path

For append-only managed branches, a new commit whose parent is the previously
verified head followed by `update_ref(force=false)` is protected against a
normal concurrent branch advance by GitHub's non-fast-forward rejection.

Therefore an executor MAY omit a redundant immediate pre-write reread when all
of these are true:

- the exact parent/head relationship was previously verified;
- the new commit is a direct descendant of that head;
- the branch is managed as append-only for the operation;
- `force=false`;
- no authorized concurrent force rewrite is expected.

Post-write verification may be coalesced with the next semantic operation that
returns/verifies the head (for example PR creation/status) rather than performed
as a dedicated read.

General ref mutation, force rewrites, arbitrary existing descendants, or
uncertain/shared mutation still require true compare-and-swap/lease semantics or
the conservative read/check/write/read path.

The connector's advertised `update_ref(expected_sha=...)` remains unusable in
the observed surface; the defect is tracked publicly as openai/codex issue
#50987. This limitation MUST NOT be represented as working CAS.

## Shared versus project-local ownership

Workspace-control may own:

- certification stage semantics;
- generic receipt/failure-envelope shape;
- operation identity/idempotency conventions;
- cache/invalidation principles;
- structured process-observation rules;
- bounded-diagnosis guidance;
- control-cycle measurements.

Owning projects retain:

- exact packages and versions;
- model/backend facts;
- prompts and domain inputs;
- scientific thresholds;
- production/materialization decisions;
- exact cache-key facts needed by the project runtime.

## Open calibration points

Wave 3 is intentionally a field-design wave, not a frozen rollout contract.

Still calibrating:

- minimum C2b engine-health proof across different runtime families;
- minimum C3 canary shape by workload modality;
- which backend/toolchain facts can be discovered statically versus only during
  engine boot;
- cache invalidation boundaries for driver/runtime/model/compiler changes;
- generic child-process failure-envelope fields;
- useful control-cycle timing instrumentation without turning main into a
  telemetry sink.

These are implementation details inside a stable architecture, not reasons to
delay field validation.

## Exit criteria for Wave 3

Wave 3 can freeze for shared implementation/rollout planning when:

1. C0-C3 semantics survive at least two materially different natural runtime
   workflows or failure classes without architectural redesign;
2. one natural retry demonstrates certified reuse/cache savings;
3. child-process/root-cause evidence avoids at least one large-log diagnosis
   cycle;
4. interruption recovery resumes from the first invalid stage without repeating
   completed expensive work;
5. bounded diagnosis demonstrably reduces root-cause-to-action control latency;
6. remaining findings are predominantly project-specific rather than new shared
   control-plane mechanisms.

Do not create the final cross-repository rollout task before these gates are met.
