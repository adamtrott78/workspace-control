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

After fresh independent review acceptance, execute exactly one bounded Lambda operator transaction: verify controller SHA256=9a262495d8c52877ad79d852dbd2a8987961dd0470c895cb39b45eb896590ed9; controller unit SHA256=76a6d05139cc38c43f474ea823cfd88514d127b9cacaf783f46a251410ad7831; maintenance service SHA256=6f37085b0b619768ef927e16c4d5e42e01090b71a7a32305b19b6e5a4cfb167c; provisioner Git blob=f0173ec2e8749699a5c94abea6d2270aa19a4387; runtime Git blob=5803ba1fedbcd66e3c9058b9d3cd32740596baad; workspace-control CPU inactive, research-engine CPU/GPU inactive, PADataset CPU/GPU active, provisioner and maintenance active, and no active transient execution; then start only workspace-ci-controller@workspace-control-cpu.service. No reset/reconcile/retrigger/research-engine mutation is authorized.

## Remaining work

- Obtain fresh authority-sensitive review of the exact 2026-11-10 start-only recovery boundary.
- On Lambda, run one fail-closed preflight that verifies known-good installed identities and service/lane state, then start only workspace-ci-controller@workspace-control-cpu.service.
- Use Workspace Shell unit_state and GitHub Actions evidence to verify controller health and run #389 acquisition/completion.
- Do not reset/reconcile/recreate scale sets, touch research-engine recovery state, or widen admission/capacity.

## Blockers / gates

- Fresh authority-sensitive review is required before today’s start-only controller mutation; historical recovery authority is retained as evidence but is not treated as perpetual execution authority.
- Operator preflight must prove exact known-good installed controller/unit/maintenance identities, control-small provisioner/runtime identities, healthy supporting services, required inactive research lanes, and no active transient execution before starting workspace-control CPU.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
