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

After corrected-head independent review acceptance, execute exactly one bounded Lambda operator transaction. Before any start, require controller SHA256=9a262495d8c52877ad79d852dbd2a8987961dd0470c895cb39b45eb896590ed9; controller unit SHA256=76a6d05139cc38c43f474ea823cfd88514d127b9cacaf783f46a251410ad7831; maintenance service SHA256=6f37085b0b619768ef927e16c4d5e42e01090b71a7a32305b19b6e5a4cfb167c; provisioner Git blob=f0173ec2e8749699a5c94abea6d2270aa19a4387; runtime Git blob=5803ba1fedbcd66e3c9058b9d3cd32740596baad; root admission policy lambda_ci_multirepo.py Git blob=cf534343119ebde2a338ea592369ce36374a88b3; workspace-control CPU inactive/dead; research-engine CPU/GPU inactive; PADataset CPU/GPU active; provisioner and maintenance active; no active transient execution. Any mismatch aborts before start and must be reported as observed evidence. If and only if every predicate passes, start only workspace-ci-controller@workspace-control-cpu.service. No reset/reconcile/retrigger/research-engine mutation is authorized.

## Remaining work

- Validate the corrected PR #597 head.
- Obtain fresh independent authority-sensitive corrected-head re-review.
- Only after acceptance, run one fail-closed Lambda preflight that hashes every authority-bearing installed component including lambda_ci_multirepo.py and verifies supporting service/lane state.
- If every predicate passes, start only workspace-ci-controller@workspace-control-cpu.service.
- Use Workspace Shell unit_state and GitHub Actions evidence to verify controller health and run #389 acquisition/completion.
- Do not reset/reconcile/recreate scale sets, touch research-engine recovery state, widen admission/capacity, or retrigger workflows.

## Blockers / gates

- Fresh corrected-head authority-sensitive re-review is required after BF-1/BF-2 corrections.
- Operator preflight must prove exact known-good controller/unit/maintenance identities; provisioner blob f0173ec2e8749699a5c94abea6d2270aa19a4387; runtime blob 5803ba1fedbcd66e3c9058b9d3cd32740596baad; and root admission-policy blob cf534343119ebde2a338ea592369ce36374a88b3. Any mismatch aborts before start.
- If lambda_ci_multirepo.py is not cf534343119ebde2a338ea592369ce36374a88b3, do not infer that 1edc048f259f86ddbf750a5534449606119b2eca is authorized; record the actual identity and open a separate provenance/installation gate.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
