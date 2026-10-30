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
- Remote checkpoint: 09216de5663718810b00f645e911e948bfeb13c0
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 94edb809f4c295902911f8cc4b3652a9121ac715
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 35e6f451fe36f039b5f6461f7469f0eed1e79e43
- Remote verified: true

## Next safe action

Resume PR #572 at exact head 09216de5663718810b00f645e911e948bfeb13c0. First fix the repository-only production-v3 launch-spec blocker exposed by Workspace Control Validation #1279 / run 40991317744: scripts/lambda_ci_v3_spec.py line 132 reads resource['runtime_seconds'], but architecture/lambda-ci-workload-policy.v1.json resource classes define max_runtime_seconds. Confirm the intended root-owned runtime bound is min(systemd_profile.RuntimeMaxSec, resource_class.max_runtime_seconds), correct the adapter and add/retain regression coverage across all nine runner classes. Then rerun exact-head validation and continue production-v3 root capacity provider/controller/reconciliation/migration tooling only if green. Do not mutate Lambda, start v3 controllers, apply PR #571, retrigger host-attest, or alter research-engine GPU containment.

## Remaining work

- Resolve the exact-head production-v3 launch-spec mismatch: use the canonical root-owned resource runtime bound (max_runtime_seconds) consistently and prove all nine runner classes build without widening authority.
- Re-run exact-head Workspace Control validation; consume any remaining production-v3 spec/controller/root-provider failures before adding migration authority.
- Complete the production v3 root capacity provider from the verified two-phase RESERVE/LAUNCH/STATUS/CANCEL model under disjoint v3 paths.
- Complete the production v3 Go runner-class controller using the pinned actions/scaleset client, TotalAssignedJobs scaling, structured trusted-workflow admission, in-process retry/backoff, and no JobDisplayName parser.
- Complete v3 reconciliation/install projections, unique controller Unix identities, project credential groups, systemd templates, tmpfiles, and disjoint persistent/runtime state.
- Generate migration-only class canary workflows and prove their payloads cannot execute candidate code or widen class authority.
- Add repository-only integration tests proving v2/v3 install-path disjointness and the generation-exclusion cutover/rollback transaction.
- Only after the production implementation candidate and migration transaction are exact-head green may any separate live activation authority be considered.

## Blockers / gates

- PR #572 exact head 09216de5663718810b00f645e911e948bfeb13c0 fails Workspace Control Validation #1279 / run 40991317744 in unit regression: 9 test_lambda_ci_v3_spec tests error at scripts/lambda_ci_v3_spec.py:132 with KeyError 'runtime_seconds'. The canonical workload resource classes use max_runtime_seconds. This is a repository-only production-v3 adapter/schema-name mismatch; no Lambda mutation is authorized.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
