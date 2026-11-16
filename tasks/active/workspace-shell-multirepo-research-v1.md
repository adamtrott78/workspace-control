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
- Remote checkpoint: ccdde5c9fa6bfe17f34adea3d6fb13d7ad9b1fbe
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: befe383fd67c8bca8d8ce370344b33c7e13cd52f
- Remote verified: true

## Next safe action

RETRY THE VALIDATED TRANSACTIONAL WORKSPACE SHELL UPGRADE from the exact authority-state head produced by this checkpoint using workspace-control runtime candidate ccdde5c9fa6bfe17f34adea3d6fb13d7ad9b1fbe, PADataset execution befe383fd67c8bca8d8ce370344b33c7e13cd52f, semantic capsule source 2cec87fbf5c054b632e5ddc7e057384e4228c48a, and semantic execution binding 9b02005a58a961ce83ef8790e2d59ec626802591. The prior activation safely rolled back because its local MCP parser incorrectly expected nested stdout that the declared MCP output schema does not guarantee. The corrected upgrader proves semantic execution using MCP success plus the root-owned execution receipt: exact task_id, expected/observed Git SHA, task checkpoint SHA, source_mode=task, exit 0 and privileged=false. Do not rebind the semantic task or widen helper/issuer trust.

## Remaining work

- In a fresh conversation, confirm workspace_shell_exec exposes candidate-pytest.
- Run candidate-pytest against PADataset Architecture-B PR #23 exact SHA 4f27d00cce9ab15120d924963a5ecf049d032c52 while durable PADataset authority remains befe383fd67c8bca8d8ce370344b33c7e13cd52f.
- Verify the candidate receipt binds durable task checkpoint + candidate SHA/tree and does not mutate authoritative task state.
- Verify ordinary task-bound execution still rejects the same off-checkpoint SHA.
- Then hand execution back to mth602-final-multisurrogate-dqnguard-v1.

## Blockers / gates

- Live semantic authority is not yet activated because the first enrollment attempt safely rolled back after a false-negative acceptance check. Corrected receipt-based acceptance candidate ccdde5c9fa6bfe17f34adea3d6fb13d7ad9b1fbe passed Workspace Control Validation #2896.
- Host activation remains a genuine root/operator step because privileged helper and trusted issuer registries intentionally remain empty. After retry success, ChatGPT must independently confirm workspace-semantic-execution-migration-v1 resolves at exact bound SHA 9b02005a58a961ce83ef8790e2d59ec626802591.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
