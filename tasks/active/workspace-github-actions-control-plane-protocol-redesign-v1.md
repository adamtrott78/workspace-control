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
- Remote checkpoint: e5a44edfd22a62b05cf730cf918b6e8aa7d534a2
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

PADataset CPU retry is safe after manual-stop recovery. Transaction b899379d-7e33-4b28-90db-10fbbcc8d24b was explicitly rolled back with V3_CANARY_ROLLBACK=PASS; GitHub run 41415414390 is completed/cancelled. Independent post-recovery attestation: v3 reconciler active/exited, v3 provisioner active/running, workspace-control v2 CPU active/running, PADataset v2 CPU diagnose 6573085129 PASS active/running with no active project units/reset/recovery conflict, Research GPU diagnose 6573086034 PASS inactive/dead+disabled with no active/pending/reset conflict. The queueing root cause is fixed at e5a44edfd22a62b05cf730cf918b6e8aa7d534a2 / Validation 41416385648: the canary preflight previously hardcoded the target scale-set repository to workspace-control; it now accepts an explicit target URL and the PADataset operator binds it to https://github.com/adamtrott78/PADataset. Next safe action: rerun the bounded PADataset CPU canary from the exact validated durable head after this recovery checkpoint is synced; retry-history must match both prior rolled-back transactions and mint a new authority.

## Remaining work

- Rerun `scripts/lambda_ci_v3_padataset_cpu_canary_live.sh` once from the exact clean validated durable head containing e5a44edfd22a62b05cf730cf918b6e8aa7d534a2.
- Require preflight output to attest `V3_SCALE_SET_TARGET_URL=https://github.com/adamtrott78/PADataset` and a PADataset target scale set before authority creation.
- After terminal CPU canary success and rollback, independently attest roots, v3 class inactivity, zero v3 residue, exact v2 restoration, and Research GPU containment; then record acceptance.
- Then stage/authorize/execute padataset-gpu-single-public-v1 under its own fresh authority.
- After PADataset CPU+GPU acceptance, execute controlled production v3 cutover and v2 retirement, then resume workspace-semantic-execution-migration-v1 umbrella work.

## Blockers / gates

- CPU canary remains unaccepted; both prior live attempts are cancelled historical runs.
- Every new CPU retry must pass retry-history and mint a fresh ACTIVATE_ONE_V3_CANARY authority; no consumed authority may be reused.
- Research CPU remains separately gated; all Research GPU-derived classes remain inherited-contained and NO_BY_DEFAULT.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
