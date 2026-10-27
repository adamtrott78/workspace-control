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
- Remote branch: gitrunner-p1-bootstrap-build-staging-fix
- Remote checkpoint: a93f82b443de236b08d7f4a4f944ad77ae563630
- Remote verified: false

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Request fresh independent corrected-head review of PR #535 after closing BF-1. Verify bootstrap authority derives exclusively from Path(__file__).resolve(); the executing file must resolve exactly to scripts/lambda_ci_p1_bootstrap_install.py under the derived repository; Git's top-level must equal that repository; the exact installer path must be tracked; expected HEAD and tracked-cleanliness checks must run against that repository; caller CWD must not be authoritative. Verify the external-copy regression fails before verify_live_fingerprint(), verify_credential_scope(), build_controller(), backup_targets(), or begin_mutation_phase(). Regression-check the previously accepted build-root chown/mode fix and all prior bootstrap preservation/rollback/dormant-activation boundaries. Do not merge or retry Lambda until NO_BLOCKING_FINDING is recorded on the exact final head.

## Remaining work

- Validate and independently review PR #530, then retry the rollback-safe P1 bootstrap installer only from the exact reviewed merge SHA; preserve the three healthy controllers and keep workspace-control dormant.
- After bootstrap PASS, issue exactly one real owner GitHub -> L0 maintenance DIAGNOSE_LANE command on issue #527 and prove the durable accepted receipt before workspace-control activation.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- Independent review 5663304360 on PR #535 old head f635d5734d50b88d2eb8a146e40575f8403e4cb1 found BF-1: privileged bootstrap source attestation was still bound to caller CWD rather than the installer file actually executing. That old head must not be merged or used for Lambda mutation.
- BF-1 is corrected on PR #535 code/test head a93f82b443de236b08d7f4a4f944ad77ae563630: authority now derives from resolved __file__, exact tracked installer path, derived Git root, expected HEAD, and tracked cleanliness. Dedicated regression proves an external/copied installer fails before live fingerprinting, credential preflight, build_controller(), backup_targets(), or begin_mutation_phase(). Exact validation run 40464399665 / job 122056286646 / run #927 completed SUCCESS. Fresh independent corrected-head review remains required before merge or live retry.
- The research-engine CPU controller remains intentionally quiesced from the accepted pre-bootstrap helper; no bootstrap path is authorized to deliberately start/restart it.
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
