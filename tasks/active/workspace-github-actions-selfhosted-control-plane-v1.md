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
- Remote checkpoint: 93bd83e6f4eb96537e622d745d991eb496d5dd4d
- Remote verified: false

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Request fresh independent review of PR #535 exact validated head after the pre-mutation build-staging correction. Verify build_controller() still runs before backup_targets()/begin_mutation_phase(), the temporary build root is chowned exactly to ci-controller and remains mode 0700 before dropping privileges, the src subtree ownership/sanitized /usr/sbin/runuser boundary is unchanged, and no service/policy/reconcile/activation authority is widened. Regression must prove build_root ownership/mode are established before the ci-controller build starts. Do not merge or retry Lambda until NO_BLOCKING_FINDING is recorded on the exact final head.

## Remaining work

- Validate and independently review PR #530, then retry the rollback-safe P1 bootstrap installer only from the exact reviewed merge SHA; preserve the three healthy controllers and keep workspace-control dormant.
- After bootstrap PASS, issue exactly one real owner GitHub -> L0 maintenance DIAGNOSE_LANE command on issue #527 and prove the durable accepted receipt before workspace-control activation.
- Activate workspace-control only as the reviewed owner-commanded same-repository CPU pilot with maxRunners=1 and manifest concurrency=1; keep automatic pull_request/push admission disabled.
- Validate live P1 filesystem isolation, CPU/RAM/runtime envelope, GPU0, exact candidate provenance, deterministic receipts, maintenance authorization/replay behavior, and clean teardown/rollback.
- After live P1 acceptance, continue the separately gated work to remove routine GitHub-hosted Actions minutes; do not remove the last bootstrap path in the same change.
- Leave P2 automatic pull_request/push admission, P3 organization migration, GitHub App credential migration, resource-aware concurrency widening, and unrelated transport cleanup unauthorized.

## Blockers / gates

- Live bootstrap retry from reviewed merge 6bd20890e2bc8a44dba8a33227cbb69b3e1368fd passed LIVE_PREFLIGHT_FINGERPRINT and GITHUB_CREDENTIAL_SCOPE_PREFLIGHT, then failed during pre-mutation Go controller build because root-created tempfile.mkdtemp build root was mode 0700/root-owned and ci-controller could not traverse to the chowned src subtree. Failure occurred before backup_targets() and begin_mutation_phase(); no Lambda host mutation occurred.
- Bounded correction is on PR #535: chown the private temporary build root to ci-controller and retain mode 0700 before runuser build. Exact code/test head 93bd83e6f4eb96537e622d745d991eb496d5dd4d passed validation run 40463460438 / job 122053213183 / run #924 SUCCESS. Fresh independent review is required before merge or live retry.
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
