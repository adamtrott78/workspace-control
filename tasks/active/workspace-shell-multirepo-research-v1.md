<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-shell-multirepo-research-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-shell-multirepo-research-v1
- Title: Workspace Shell multi-repo PADataset research access v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Extend the live Workspace Shell v1 lineage with first-class PADataset access and a permanent candidate-evidence path that can validate exact candidate SHAs without promoting them to durable task authority, while preserving credential isolation, private-repository support, rollback, and exact-SHA authoritative execution.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-shell-candidate-evidence-current-v1
- Remote checkpoint: cd009257e08b2bd9f3ac241657895d3ba58c5979
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: befe383fd67c8bca8d8ce370344b33c7e13cd52f
- Remote verified: true

## Next safe action

APPLY THE VALIDATED TRANSACTIONAL WORKSPACE SHELL UPGRADE from the exact authority-state head produced by this checkpoint using workspace-control runtime candidate cd009257e08b2bd9f3ac241657895d3ba58c5979, PADataset execution befe383fd67c8bca8d8ce370344b33c7e13cd52f, semantic capsule source 2cec87fbf5c054b632e5ddc7e057384e4228c48a, and semantic execution binding 9b02005a58a961ce83ef8790e2d59ec626802591. The upgrader must preserve rollback, import only the fixed semantic task capsule, prove its capsule binding, and run a live workspace_shell_exec git-read returning exactly 9b02005a58a961ce83ef8790e2d59ec626802591. Do not add trusted issuers/helpers or rebind the semantic task.

## Remaining work

- In a fresh conversation, confirm workspace_shell_exec exposes candidate-pytest.
- Run candidate-pytest against PADataset Architecture-B PR #23 exact SHA 4f27d00cce9ab15120d924963a5ecf049d032c52 while durable PADataset authority remains befe383fd67c8bca8d8ce370344b33c7e13cd52f.
- Verify the candidate receipt binds durable task checkpoint + candidate SHA/tree and does not mutate authoritative task state.
- Verify ordinary task-bound execution still rejects the same off-checkpoint SHA.
- Then hand execution back to mth602-final-multisurrogate-dqnguard-v1.

## Blockers / gates

- The semantic-enrollment runtime candidate is repository-validated, but live host activation still requires the transactional root-owned Workspace Shell upgrader. Privileged helper registry and trusted issuer registry are intentionally empty, so ChatGPT cannot perform that sudo/root activation through Workspace Shell.
- After host activation, live acceptance must prove workspace-semantic-execution-migration-v1 resolves and git-read observes exact bound workspace-control HEAD 9b02005a58a961ce83ef8790e2d59ec626802591; do not proceed on capsule-resolution alone.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
