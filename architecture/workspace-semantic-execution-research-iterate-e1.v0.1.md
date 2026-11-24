# Integrated Research-Iterate E1 v0.1

Status: **IMPLEMENTATION CONTRACT / NON-AUTHORITY**

Parent task: `workspace-semantic-execution-migration-v1`

## Goal

Exercise the real semantic-execution system as a mission rather than a bridge calibration. E1 proves root decomposition, mixed deterministic/Instant routing, exact-source provenance, one harmless connected Workspace Shell read-only leaf, fan-in, and final Instant synthesis through the accepted Operator Bridge.

## Required topology

1. Root decomposer — Instant. It publishes `TOO_LARGE` and creates exactly three inherited child processes: exact-source, analysis, and Workspace Shell probe.
2. Exact-source leaf — deterministic. It reads the frozen Research Engine orchestration fixture at `research-engine@1031861c03b2af8cff5cf72939bbbc83a95e65a4` and validates immutable provenance without a model invocation.
3. Analysis leaf — Instant. It reasons over the exact-source evidence and publishes one immutable candidate via literal `@github`.
4. Workspace Shell probe — Instant. Its objective begins with literal `@Workspace Shell` and `@github`, invokes only `workspace_shell_inspect(task_id="workspace-semantic-execution-migration-v1", target="workspace-shell", operation="runtime_inventory")`, and publishes the SHA-256 of canonical JSON returned by that read-only call.
5. Fan-in — deterministic. Root remains waiting until all three required children are durably complete/validated. No model polling while waiting.
6. Synthesis — Instant. Root resumes only from child receipts/provenance and publishes the final mission result.

## Workspace Shell proof boundary

The Workspace Shell leaf may use only the typed read-only `workspace_shell_inspect` operation above. `workspace_shell_exec`, `workspace_shell_run_reviewed_helper`, service mutation, repository mutation, privileged execution, and authority widening are prohibited. The expected runtime-inventory digest is validator-side evidence and is not disclosed in the worker packet.

The current control-side observation is canonicalized with JSON `sort_keys=true` and separators `(",", ":")`; its SHA-256 is bound by the E1 review/authority, not supplied to the worker.

## Supervisor S1

The first Supervisor slice is read-only and projection-only. It must be able to reconstruct from durable state: mission objective, completed/running/waiting work, current critical path, blockers, pending human decisions, validated versus proposed claims, and provenance. Conversation memory is a cache only and it makes zero authority/task mutations.

## E1 acceptance

- root `TOO_LARGE` decomposition is durably accepted;
- deterministic exact-source leaf completes with independent provenance validation;
- normal Instant analysis leaf completes;
- exact literal `@Workspace Shell` produces the hidden expected runtime-inventory digest;
- exact literal `@github` publishes the Workspace Shell leaf candidate without Tab/autocomplete selection;
- no Workspace Shell exec/helper/mutation path is used;
- fan-in waits for all three leaves;
- final Instant synthesis completes from validated child evidence;
- no stale generation acceptance, paid API fallback, ChatGPT page inspection, or manual durable-state relay;
- Supervisor S1 can be rebuilt from durable state after a fresh session.

## Separation

E1 is mixed-routing/fan-in/synthesis. E2 is deliberate worker/session/process loss and durable recovery. E3 is resource accounting and soak. E1 must not silently absorb E2/E3.
