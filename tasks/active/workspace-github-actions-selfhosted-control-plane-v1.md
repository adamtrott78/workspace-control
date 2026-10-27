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
- Remote branch: gitrunner-p1-bootstrap-shared-restart-recovery
- Remote checkpoint: 58ff087133f914bb1bac7a929ecf4cd45677334a
- Remote verified: false

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Request fresh independent review of PR #536. Verify the post-rollback diagnosis against the captured incident evidence: the three non-CPU project controllers were active pre-mutation, all became inactive/dead with ExecMainStatus=0 and NRestarts=0 at the exact shared-provisioner rollback window, and research-engine GPU journal records an explicit systemd stop rather than a crash. Review the bootstrap correction: maintenance identity uses actual group membership rather than primary-GID equality; after a shared provisioner restart, only non-CPU controllers that were active/running in the pre-mutation snapshot and are now exactly loaded+enabled+inactive/dead+ExecMainStatus=0 with unchanged NRestarts may be started; research-engine CPU remains preservation-only and cannot be started/restarted. Review the one-shot incident helper: exact source binding, exact current CPU/target incident states, shared services active, no project execution, sole mutation one systemctl start of exactly research-engine-gpu + padataset-cpu + padataset-gpu, followed by active/running verification. Do not merge or mutate Lambda until NO_BLOCKING_FINDING is recorded on the exact final head.

## Remaining work

- Validate and independently review PR #530, then retry the rollback-safe P1 bootstrap installer only from the exact reviewed merge SHA; preserve the three healthy controllers and keep workspace-control dormant.
- After bootstrap PASS, issue exactly one real owner GitHub -> L0 maintenance DIAGNOSE_LANE command on issue #527 and prove the durable accepted receipt before workspace-control activation.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- Post-rollback read-only fingerprint proved rollback restored bootstrap-created files/state and removed ci-maintenance, but all three previously healthy non-CPU project controllers were cleanly dependency-stopped at 03:11:30 when rollback restarted the shared provisioner required by their unit template. Research-engine CPU remained intentionally quiesced and unchanged.
- PR #536 contains the bounded correction and incident recovery path. Exact code/test head 58ff087133f914bb1bac7a929ecf4cd45677334a passed validation run 40466539746 / job 122063195362 / run #929 SUCCESS. Fresh independent review remains required before merge or any Lambda recovery mutation.
- No bootstrap retry, workspace-control activation, reconciliation, L0 diagnose, or research-engine CPU restart is authorized until PR #536 exact final head receives NO_BLOCKING_FINDING and the bounded recovery helper restores the three dependency-stopped controllers.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
