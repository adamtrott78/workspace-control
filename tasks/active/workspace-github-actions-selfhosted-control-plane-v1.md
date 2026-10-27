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
- Remote branch: gitrunner-p1-quiesce-source-binding-v2
- Remote checkpoint: dca9ae15e1e9d53283ef8ed1d4a57ccddb80abba
- Remote verified: false

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Request fresh independent corrected-head review of PR #534. Verify BF-1 is closed by binding source attestation to Path(__file__).resolve(), requiring the executing file to resolve exactly to scripts/lambda_ci_p1_quiesce_restart_storm.py under the derived repository, requiring Git's top-level to equal that derived repository, requiring that helper path to be tracked, and performing expected-HEAD/tracked-cleanliness checks against that repository. Verify regression tests prove an external/copied helper cannot pass attestation or reach quiesce_and_verify(). Re-review all previously accepted restart-storm proof and exact single-service-stop boundaries. Do not merge or mutate Lambda unless the exact corrected head receives NO_BLOCKING_FINDING.

## Remaining work

- Validate and independently review PR #530, then retry the rollback-safe P1 bootstrap installer only from the exact reviewed merge SHA; preserve the three healthy controllers and keep workspace-control dormant.
- After bootstrap PASS, issue exactly one real owner GitHub -> L0 maintenance DIAGNOSE_LANE command on issue #527 and prove the durable accepted receipt before workspace-control activation.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- Independent review 5662986453 on blocked PR #533 head f78e38859f6dec44e88c45d8e9c648b04c487fbb found BF-1: source attestation was bound to caller CWD rather than the executing helper file. That old head must never be used for Lambda mutation.
- PR #533 was accidentally squash-merged as 5056304df6d5bca925fa1a4cff2ed6b1d8948242 without closing BF-1. Main was immediately restored to the exact pre-#533 tree by revert commit 0d84ac243f1dbd883e1fcd23a3b08f57378148db. No Lambda mutation occurred.
- Corrected source-binding implementation is on PR #534. Exact code/test head dca9ae15e1e9d53283ef8ed1d4a57ccddb80abba passed run 40461478870 / job 122046888412 / run #920 SUCCESS. Fresh independent corrected-head review remains required before merge or live quiesce.
- The independently reviewed P1 bootstrap merge 6bd20890e2bc8a44dba8a33227cbb69b3e1368fd remains unchanged and is the intended bootstrap executable only after accepted quiesce.
- workspace-control activation remains separately blocked until bootstrap install passes and a real GitHub -> L0 maintenance DIAGNOSE_LANE command produces a durable accepted receipt.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
