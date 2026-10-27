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
- Remote branch: github-actions-selfhosted-control-plane-v02
- Remote checkpoint: b7e8a0199e2ccd79f8787e9f95faa28365d3b216
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 0badc99b894d87413d065afdcd37a678c2839007
- Remote verified: true

## Next safe action

Perform a fresh independent preimplementation review of architecture/github-actions-selfhosted-control-plane.v0.2.json@2866f7d76aed0d5792b86ea175e9492c90115f50 together with the deliberately unchanged NOT_INSTALLED workspace-control manifest architecture/lambda-ci-project-workspace-control.v1.json@efa6e09f4206ca1d1d2fe6daaabcb69ed01d4588. The reviewer must explicitly verify BF-1 resolution (TotalAssignedJobs is non-authoritative for execution; fail-closed assignment-divergence quarantine; exact stale scale-set reset with local quiescence, fresh scale-set identity, two zero-state observations, durable receipt, and single-retry gate) and BF-2 resolution (independently installed L0 maintenance path; finite typed verbs; derived targets; SO_PEERCRED/root validation; replay-safe receipts; no arbitrary shell/path/systemd/property/credential surface; no L1 self-repair circularity). Also re-check workspace-control isolation, maxRunners=1/concurrency=1 P1 limit, transport/execution separation, independent bootstrap, P2/P3 deferral, and rollback. Persist NO_BLOCKING_FINDING or exact blockers. Do not implement or activate P1 until that disposition is durably consumed.

## Remaining work

- Obtain and durably consume a fresh independent review of the exact v0.2 architecture and unchanged NOT_INSTALLED workspace-control manifest.
- If v0.2 receives NO_BLOCKING_FINDING, implement only P1: admission-v2 assignment-divergence quarantine/recovery, bounded independently installed L0 maintenance path, and owner-commanded workspace-control JIT CPU validation pilot.
- Validate P1 implementation with adversarial stale-assignment/replay/maintenance-authority tests, filesystem isolation, CPU/RAM/runtime envelope, no-GPU guarantee, receipts, rollback, and independent bootstrap availability.
- Do not raise maxRunners or manifest concurrency until separately reviewed resource-aware host arbitration is designed and validated.
- Design/review automatic pull_request/push admission as P2 only after P1 succeeds.
- Keep GitHub organization migration, runner-group IDs, organization registration, attestation migration, and least-privilege GitHub App credentials in separately reviewed P3.
- Retire temporary public workspace-control and research-engine GPU-listener transport only after reviewed replacement paths are live and rollback-safe.

## Blockers / gates

- Live P1 implementation/activation is blocked pending fresh independent preimplementation review of architecture/github-actions-selfhosted-control-plane.v0.2.json@2866f7d76aed0d5792b86ea175e9492c90115f50 plus unchanged architecture/lambda-ci-project-workspace-control.v1.json@efa6e09f4206ca1d1d2fe6daaabcb69ed01d4588.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
