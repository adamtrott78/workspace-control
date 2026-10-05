# Runtime Certification and Resumable Heavyweight Execution

Status: **Wave-3 design candidate**

Implements `architecture/throughput-runtime-certification-wave3.md`.

## When this procedure applies

Use this procedure for heavyweight or failure-prone runtimes where environment
construction, model/engine startup, compilation/JIT, external services, or remote
execution are expensive enough that repeated discovery materially affects the
control cycle.

Do not impose it on trivial scripts whose complete execution is cheaper than the
certification machinery.

## 1. Establish authority and operation identity

Before runtime work:

1. establish task/repository/daemon/production authority;
2. establish exact source Git state;
3. compute or recover the owning operation identity;
4. inspect any durable receipt for that operation;
5. resume from the first invalid or failed stage.

Do not rerun a completed stage merely to collect efficiency telemetry.

## 2. C0 — aggregate static closure

Collect exact package/runtime identity and resolve as much dependency closure as
is cheaply observable.

Check, when material:

- package/lock/wheel hashes;
- Python/OS/architecture ABI;
- accelerator and driver/runtime compatibility;
- native shared-library dependencies;
- required external binaries/compilers/headers/services;
- model/config hashes needed by the engine identity;
- selected or deterministically resolvable backend requirements.

Return all independent defects that can be established in one pass. Do not exit
on the first missing library if additional independent checks are safe and cheap.

Write a C0 receipt whether PASS or ordinary observable FAIL.

## 3. C1 — exact import and accelerator smoke

Using the actual runtime:

1. import the same library/module path used by the workload;
2. confirm exact expected package identity;
3. prove accelerator visibility;
4. perform one bounded real allocation;
5. release the probe allocation.

Write a C1 receipt.

A passing C1 MUST be described as import/accelerator certification only.

## 4. C2a — resolve execution backend/toolchain plan

Resolve dynamic/optional backend choices before expensive engine boot whenever
the runtime exposes enough information to do so.

Record the selected backend plan and its additional requirements.

If the preferred/default backend requires an unavailable optional toolchain, a
different supported backend may be selected only when the owning project proves
that the change preserves the workload's semantic contract. Record the choice in
execution identity.

Fail before engine boot when an unavoidable selected dependency is known to be
missing.

## 5. C2b — boot the real engine

Instantiate the same engine/model configuration required by the workload.

Capture:

- start/end/health state;
- child process roles and exits;
- model/config/tokenizer/processor identity;
- compile/JIT/cache behavior;
- resource observations;
- first causal failure.

On failure, do not proceed to domain work. Preserve successful earlier receipts
and the failure envelope.

## 6. C3 — synthetic same-modality canary

After healthy engine boot, execute one minimal deterministic request through the
same modality/request path.

The canary should be generated locally, cheap, non-scientific, and structurally
representative.

Require a completed request and valid response shape. The owning project may add
resource ceilings if necessary for safe operation.

Only after C3 passes may the runtime-certified sentinel be written.

## 7. Reuse and invalidation

On later runs:

1. recompute execution identity;
2. re-evaluate compatibility predicates;
3. verify certification receipts/sentinel;
4. reuse C0-C3 only when all required identity and host predicates still hold.

Invalidate from the earliest affected stage. Do not automatically invalidate all
later stages for irrelevant run-artifact changes.

## 8. Persistent caches

Store expensive reusable compile/JIT/runtime cache state outside timestamped run
output when complete identity and invalidation rules exist.

Record cache key/identity and hit/miss evidence.

Never copy an old cache into a new identity merely to manufacture a performance
result.

## 9. Domain execution

Only after valid required certification:

- verify/materialize domain inputs;
- execute the real benchmark/workload;
- preserve project-local provenance and quality gates.

Runtime certification does not authorize production routing, scientific-state
materialization, or other project-owned actions.

## 10. Failure handoff

Ordinary failure handoff should include:

1. compact stage receipt/failure envelope;
2. first causal error;
3. targeted log excerpt only when needed;
4. full log/artifact path for deeper diagnosis.

Do not paste or retrieve the full console log by default.

## 11. Interruption recovery

Recovery should be bounded:

1. inspect durable task/source/operation receipts;
2. inspect structural process/service identity only for stages that may still be
   RUNNING;
3. resume from the first unfinished/invalid stage.

Avoid giant recovery wrappers that recompute already-durable state.

Process detection must use executable/argv/pid/service identity, not substring
matching over flattened shell command lines.

## 12. Actionability gate

When the first causal failure, bounded correction, and governing invariants are
known, stop broad diagnosis.

Checkpoint the evidence, apply or return the bounded correction, and continue
from the failed certification stage.

Additional exploration is justified only when required for safety/correctness or
when new evidence contradicts the current diagnosis.

## 13. Measurement

For each natural field run record when available:

- time and result for C0/C1/C2a/C2b/C3;
- setup/download/cache work avoided;
- compile/JIT cache cold versus reuse cost;
- engine boot cost;
- number of failed control cycles before root cause;
- receipt bytes versus full log bytes;
- connector reads/writes and Git commits;
- human terminal handoff time;
- first-sufficient-root-cause to durable-correction time.

Do not create benchmark-only churn solely to improve these measurements.
