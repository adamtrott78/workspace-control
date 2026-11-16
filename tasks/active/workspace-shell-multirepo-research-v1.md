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

RETRY THE VALIDATED TRANSACTIONAL WORKSPACE SHELL UPGRADE from the exact authority-state head produced by this checkpoint using workspace-control runtime candidate ccdde5c9fa6bfe17f34adea3d6fb13d7ad9b1fbe, PADataset execution befe383fd67c8bca8d8ce370344b33c7e13cd52f, semantic capsule source 629cbb10cd3e7136a34faa2df575ca3b5d481b80, and semantic execution binding 74958b5d0d325893fd39045d1e49b5320dca7fa3. This intentionally supersedes the older semantic capsule/execution tuple 2cec87fb… / 9b02005a…. The current semantic state is 3/3 green (#2900/#225/#503) and includes the evaluator sealed-store primitive plus claim-bearing launch isolation gate. The corrected Workspace Shell runtime candidate is green at #2896. Require LOCAL_SEMANTIC_TASK_MCP=PASS, LOCAL_SEMANTIC_TASK_RECEIPT=PASS, LOCAL_SEMANTIC_TASK_AUTHORITY=PASS and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS. Do not rebind the semantic task, widen helper/issuer trust, or touch PADataset GPUs.

## Remaining work

- In a fresh conversation, confirm workspace_shell_exec exposes candidate-pytest.
- Run candidate-pytest against PADataset Architecture-B PR #23 exact SHA 4f27d00cce9ab15120d924963a5ecf049d032c52 while durable PADataset authority remains befe383fd67c8bca8d8ce370344b33c7e13cd52f.
- Verify the candidate receipt binds durable task checkpoint + candidate SHA/tree and does not mutate authoritative task state.
- Verify ordinary task-bound execution still rejects the same off-checkpoint SHA.
- Then hand execution back to mth602-final-multisurrogate-dqnguard-v1.

## Blockers / gates

- Live semantic authority is not yet activated because the first enrollment attempt safely rolled back on a false-negative acceptance parser. Corrected receipt-based runtime candidate ccdde5c9fa6bfe17f34adea3d6fb13d7ad9b1fbe passed Workspace Control #2896.
- The semantic enrollment tuple has advanced to current validated semantic capsule 629cbb10cd3e7136a34faa2df575ca3b5d481b80 with exact execution binding 74958b5d0d325893fd39045d1e49b5320dca7fa3 (#2900/#225/#503). Host activation remains a root/operator step because helper/issuer trust remains intentionally empty.
- After retry success, ChatGPT must independently verify the semantic task resolves at exact HEAD 74958b5d0d325893fd39045d1e49b5320dca7fa3 before any live transport/evaluator acceptance work.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
