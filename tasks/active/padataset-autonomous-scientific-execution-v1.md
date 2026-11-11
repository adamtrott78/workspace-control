<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: padataset-autonomous-scientific-execution-v1
- Title: PADataset autonomous scientific execution v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Make PADataset scientific GPU experiments autonomously executable by ChatGPT through the existing self-hosted Lambda control plane using an exact root-owned DNNs runtime, exact PR-head provenance, read-only project data/cache authority, bounded experiment request schemas, durable artifacts/receipts, and no per-run operator terminal work.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: padataset-autonomous-scientific-execution-v1
- Remote checkpoint: 313e204d7342c0c14b00c2956401783d39e02d9b
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 100888178f362094c45807817f992d2653dcb7b2
- Remote verified: true

## Next safe action

Read-only diagnose the uniquely resolved DNNs prefix /home/atrott/adamArchives/venvs/DNNs before changing or rerunning the promoter. Establish the actual environment type and why `conda list --prefix /home/atrott/adamArchives/venvs/DNNs --json` fails. Then implement a fail-closed immutable promotion path appropriate to that environment, validate the new exact head, and only then request the one-time root bootstrap.

## Remaining work

- Read-only diagnose /home/atrott/adamArchives/venvs/DNNs: determine whether it is a Conda env, Python venv, or other environment; inspect sys.prefix/base_prefix, pyvenv.cfg, conda-meta presence, interpreter path, scientific imports/CUDA, and the exact Conda list failure without mutating the environment.
- Choose the smallest reproducible immutable promotion mechanism supported by the actual environment type. Do not fall back to mounting the mutable user environment into routine jobs.
- Implement the corrected promoter on padataset-autonomous-scientific-execution-v1, add regression coverage, and pass exact-head workspace-control validation before another operator attempt.
- After one-time promotion succeeds, commit exact DNNs runtime/data bindings, activate the scientific contract/route, validate and reconcile live.
- Then ChatGPT creates the Stage03 experiment request, triggers autonomous scientific smoke, full PA2 backbone training, and Architecture C evaluation.

## Blockers / gates

- The actual DNNs runtime is uniquely resolved at /home/atrott/adamArchives/venvs/DNNs, but the current promoter assumes that exact prefix is readable/cloneable by Conda. That assumption is false on this machine.
- Do not retry the current promoter and do not perform root mutation until the environment type and reproducible immutable-copy/clone mechanism are diagnosed read-only and a replacement candidate passes exact-head validation.
- Routine scientific execution remains disabled until a root-owned immutable DNNs runtime and Stage03 cache are promoted, bound, validated, activated, and reconciled.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/padataset-autonomous-scientific-execution-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
