<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-github-actions-selfhosted-control-plane-v1
- Title: GitHub Actions Self-Hosted Control Plane v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Eliminate routine dependence on metered GitHub-hosted runners by moving workspace-control and project CI onto bounded self-hosted Lambda execution while preserving a non-circular bootstrap authority, per-project isolation, fail-closed admission, review gates, and a clean path to GitHub organization runner groups. Also reduce operator copy/paste by making review targets and dispositions durable and GitHub-native.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 4d98555a678050e611502de1b9b8c35b4cf9c5fa
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

After fresh corrected-head review acceptance, execute one bounded Lambda transaction. Require exact controller/unit/maintenance/provisioner/runtime/root-policy identities already frozen. Require workspace-control CPU inactive/dead and research-engine CPU/GPU inactive/dead. Require provisioner and maintenance active/running and no active transient project execution. For each PADataset CPU/GPU controller, accept only either (a) active/running, ExecMainStatus=0, MainPID>0, or (b) inactive/dead, ExecMainStatus=0, MainPID=0; reject failed, activating, deactivating, or any nonzero ExecMainStatus. Persist the exact pre-start PADataset CPU/GPU systemctl-show snapshots. If and only if all predicates pass, start only workspace-ci-controller@workspace-control-cpu.service. After start, require workspace-control CPU active/running and require both PADataset snapshots to match their pre-start values exactly. Do not mutate PADataset, research-engine, scale sets, reconciliation, admission, capacity, or workflow trigger state.

## Remaining work

- Run the reviewed root preflight with PADataset stable-state snapshot capture.
- If every predicate passes, start only workspace-ci-controller@workspace-control-cpu.service.
- Verify workspace-control CPU active/running and PADataset CPU/GPU full snapshots unchanged.
- Observe run #389 for runner acquisition/completion and record recovery receipt.

## Blockers / gates

- Only the reviewed root-only operator transaction remains. Connected Workspace Shell cannot inspect sibling PADataset/research-engine/provisioner units or /opt authority-bearing files because they are outside its root-owned allowlist/sandbox.
- Any live identity/state mismatch aborts before start. No reset/reconcile/recreate/retrigger/PADataset/research-engine mutation is authorized.
