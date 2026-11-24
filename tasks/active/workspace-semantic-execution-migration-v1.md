<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view. Authoritative capsule: `tasks/active/workspace-semantic-execution-migration-v1.json`.

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Current state

- Task: `workspace-semantic-execution-migration-v1`
- Status: **IN_PROGRESS**
- Current stage: **November Integrated v0 delivery**
- E1: **PASS**
- E2: **PASS**
- E2 closeout head: `090155abc1c943e629d2a9fa1e74c6cf2c8927f4`
- E2 final candidate head: `6115b48dfdf4a4954b3b1626598f897e4e71eeec`

## Next safe action

E3 RESOURCE/ACCOUNTING + SOAK. E1 and E2 are accepted and must not be redone absent a demonstrated regression. Start with E3-C1: implement a read-only versioned resource observer for CPU/RAM/process/task/session/action accounting and deterministic tests proving zero semantic mutation. Then run E3-C2 bounded no-model soak with resource/leak evidence. Only after C1/C2 pass, freeze a live E3 review and stop at a fresh explicit one-shot authority gate before any live Instant soak.

## Remaining work

- E3-C1: implement and validate the read-only resource/accounting observer and machine-readable report.
- E3-C2: execute a bounded deterministic/fake-worker soak with zero model calls/GPU use; capture CPU/RAM/process/FD/thread/task/session/action trends and cleanup evidence.
- E3-LIVE: after C1/C2 and a frozen review, obtain fresh explicit operator approval for one bounded live resource/soak run; bind report to exact source/authority/candidate heads.
- E4: run calibrated economics comparison versus all-strong/frontier control only when comparable allowance telemetry is available.
- E5: run authoritative target-machine UX-09 performance benchmark.
- E6: mechanically audit exact SHA/blob/route provenance, authority boundaries, rollback paths and unresolved violations.
- E7: reconcile every November acceptance-matrix requirement to PASS or explicit promotion blocker.
- E8: record explicit integrated PROMOTE_V0 / HOLD / REVISE verdict.

## Current gates

- E3 LIVE AUTHORITY: none exists. Repository-only E3-C1/C2 work may proceed; any live E3 run requires a separately frozen review and fresh explicit operator approval.
- E4 ECONOMICS: claim-bearing comparison remains gated on calibrated comparable allowance telemetry; do not substitute raw token estimates or uncalibrated UI observations.

## Fresh-chat initialization

@GitHub
@Workspace Shell

Continue the durable workspace-control task `workspace-semantic-execution-migration-v1`.

Read:
- `tasks/active/workspace-semantic-execution-migration-v1.json`
- `architecture/workspace-semantic-execution-research-iterate-e2-live-closeout.v0.2.json`
- `architecture/workspace-semantic-execution-research-iterate-e3.v0.1.json`
- `architecture/workspace-semantic-execution-post-e2-executor-handoff.v0.1.md`

Recover the exact current Git head first. Do not redo D4/E1/E2. Begin with E3-C1 repository-safe resource observer/accounting work.
