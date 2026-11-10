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

Execute the exact reviewed root-only preflight from PR #597 head 1db6e45c8fb6d03e470aebbddf27d31790a3f801. Require controller SHA256 9a262495d8c52877ad79d852dbd2a8987961dd0470c895cb39b45eb896590ed9; controller-unit SHA256 76a6d05139cc38c43f474ea823cfd88514d127b9cacaf783f46a251410ad7831; maintenance SHA256 6f37085b0b619768ef927e16c4d5e42e01090b71a7a32305b19b6e5a4cfb167c; provisioner Git blob f0173ec2e8749699a5c94abea6d2270aa19a4387; runtime Git blob 5803ba1fedbcd66e3c9058b9d3cd32740596baad; root-policy Git blob cf534343119ebde2a338ea592369ce36374a88b3; workspace-control CPU inactive/dead; research-engine CPU/GPU inactive; PADataset CPU/GPU active/running; provisioner and maintenance active/running; and no active transient project execution. Abort on any mismatch. If all pass, start only workspace-ci-controller@workspace-control-cpu.service. No reset/reconcile/recreate/retrigger/research-engine mutation.

## Remaining work

- Run the reviewed fail-closed root preflight on Lambda.
- If and only if every exact identity/state predicate passes, start only workspace-ci-controller@workspace-control-cpu.service.
- Immediately verify the controller through Workspace Shell and observe run #389 for runner acquisition/completion.
- Record the live recovery receipt and disposition in durable task state.

## Blockers / gates

- Root-only live preflight remains required before start: exact installed controller/unit/maintenance SHA256 identities; provisioner/runtime/root-policy Git blobs; required sibling lane/service states; and no active transient execution.
- Connected Workspace Shell can directly prove workspace-control CPU is loaded/inactive/dead/MainPID=0 and maintenance is active/running, but intentionally cannot read /opt provisioner/controller files or sibling controller units; those predicates must be proved in the reviewed operator transaction.
- Any live identity/state mismatch aborts before controller start. No reset/reconcile/recreate/retrigger/research-engine mutation is authorized.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
