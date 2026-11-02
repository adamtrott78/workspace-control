<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-github-actions-control-plane-protocol-redesign-v1
- Title: GitHub Actions Control-Plane Protocol Redesign v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Replace the current parser-chained GitHub Actions runner admission path with a formally modeled, versioned, typed control-plane protocol whose routing, authority, scheduling, provisioning, execution, recovery, and lifecycle semantics are explicit end-to-end, so any executor request admitted by policy cannot later be falsely rejected by a downstream parser that implements a different grammar.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: eae9ba119ace3fc1acba4642c577c1454a03a064
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 6165556086b73d2076f205f11ec7b988150f23dd
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 35e6f451fe36f039b5f6461f7469f0eed1e79e43
- Remote verified: true

## Next safe action

PADATASET CPU CANARY PRE-AUTHORITY VERIFIER DRIFT FIXED. The first PADataset CPU canary attempt stopped before `CANARY_AUTHORITY_CREATED=PASS`, before `--apply-canary`, and before any workflow dispatch because `lambda_ci_v3_controller_refresh.py --verify-active` still independently required all non-controller installed artifacts to equal the immutable base and therefore rejected the legitimate reconciler live override. Live roots remained healthy; GitHub shows no PADataset canary workflow_dispatch run. Exact fix eae9ba119ace3fc1acba4642c577c1454a03a064 delegates installed-generation truth to the reconciler's shared override-aware `verify_installed()` and retains only controller-specific provenance checks in controller-refresh. Workspace Control Validation 41413372028 SUCCESS. Next safe action: rerun the same bounded PADataset CPU operator from an exact clean checkout of the new validated durable head after task-state sync; it will again create no authority until all preflights pass.

## Remaining work

- Rerun `scripts/lambda_ci_v3_padataset_cpu_canary_live.sh` once from the exact clean validated durable head containing eae9ba119ace3fc1acba4642c577c1454a03a064. The corrected controller-refresh preflight now delegates effective-generation verification to the reconciler and then verifies exact controller source/base provenance.
- After terminal canary completion and rollback, independently attest root services, every v3 class inactive, zero v3 resource/transient residue, exact v2 controller restoration, and Research GPU containment; record canary run/transaction evidence.
- Then stage/authorize/execute padataset-gpu-single-public-v1 under a separate fresh authority.
- After PADataset CPU+GPU acceptance, execute controlled production v3 cutover and v2 retirement, then resume workspace-semantic-execution-migration-v1 umbrella work.

## Blockers / gates

- No live mutation blocker remains from the failed attempt: it failed before fresh canary authority creation, generation-exclusion transaction apply, or workflow dispatch.
- A single operator-root rerun of the corrected PADataset CPU canary script is still required because Workspace Shell has no accepted privileged helper/signature for this transaction.
- Research CPU remains separately gated; all Research GPU-derived v3 classes remain inherited-contained and NO_BY_DEFAULT.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
