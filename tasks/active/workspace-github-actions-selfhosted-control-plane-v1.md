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

Read-only incident inspection only. From Lambda, without starting/stopping/restarting/reloading any service, capture: systemctl show for workspace-ci-maintenance.service, workspace-ci-provisioner.service, workspace-ci-reconciler.service, workspace-ci-reconcile-controller.service, workspace-ci-controller@research-engine-cpu.service, workspace-ci-controller@research-engine-gpu.service, workspace-ci-controller@padataset-cpu.service, and workspace-ci-controller@padataset-gpu.service using LoadState,UnitFileState,ActiveState,SubState,ExecMainStatus,NRestarts; `ls -ld /run/workspace-ci /run/workspace-ci/maintenance` and `ls -l /run/workspace-ci/maintenance/maintenance.sock` if present; `journalctl -u workspace-ci-maintenance.service -n 120 --no-pager`; `journalctl -u workspace-ci-controller@research-engine-gpu.service -n 120 --no-pager`; and existence/hash/identity checks sufficient to determine whether rollback restored bootstrap-created files/users/groups. Return the complete read-only output. Do not perform recovery or retry before that evidence is durably accepted.

## Remaining work

- Perform read-only post-incident fingerprinting only: inspect maintenance root unit state, maintenance socket path, recent maintenance-root journal, provisioner/reconciler/reconcile-controller state, all four preserved controller snapshots, recent research-engine GPU journal, and rollback-restored bootstrap-created filesystem/identity state. Do not start/restart/stop/reload anything.
- Use that evidence to determine whether the maintenance-root failure is a readiness race or a daemon/service failure, and why research-engine GPU entered failed/failed during rollback.
- Design the narrow correction only after the live evidence is frozen; validate and independently review it before any recovery mutation or bootstrap retry.
- After a corrected bootstrap PASS, issue exactly one real owner GitHub -> L0 maintenance DIAGNOSE_LANE command on issue #527 and prove the durable accepted receipt before workspace-control activation.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- The exact reviewed P1 bootstrap from 4d98555a678050e611502de1b9b8c35b4cf9c5fa crossed mutation and failed at the maintenance-root readiness gate with `maintenance root socket missing`; rollback could not certify completion because research-engine GPU ended loaded+enabled+failed/failed, ExecMainStatus=1, NRestarts=0.
- No recovery, bootstrap retry, reconciliation, GitHub -> L0 command, workspace-control activation, or research-engine CPU restart is authorized until a read-only post-incident fingerprint establishes exact service/file/identity state and recent journals for the maintenance root and research-engine GPU.
- Static inspection of the reviewed implementation shows a plausible startup-readiness race: workspace-ci-maintenance.service is Type=simple, the installer checks `systemctl is-active` immediately after `enable --now`, and then immediately requires `/run/workspace-ci/maintenance/maintenance.sock` with no readiness wait. This is a hypothesis pending live journal/state evidence, not yet an accepted root cause.
- workspace-control activation remains separately blocked until a corrected bootstrap install passes and a real GitHub -> L0 maintenance DIAGNOSE_LANE command produces a durable accepted receipt.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
