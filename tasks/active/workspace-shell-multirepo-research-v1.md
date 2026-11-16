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
- Remote checkpoint: 6d47e3eca88150c6ad127b6e5901936323fe3ca1
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: befe383fd67c8bca8d8ce370344b33c7e13cd52f
- Remote verified: true

## Next safe action

RUN ONE VALIDATED ROOT ACTIVATION WINDOW from the exact authority-state head produced by this checkpoint using workspace-control runtime candidate 6d47e3eca88150c6ad127b6e5901936323fe3ca1, PADataset execution befe383fd67c8bca8d8ce370344b33c7e13cd52f, semantic capsule source 629cbb10cd3e7136a34faa2df575ca3b5d481b80, and semantic execution binding 74958b5d0d325893fd39045d1e49b5320dca7fa3. Candidate 6d47e3ec passed Workspace Control #2902 and bundles both semantic authority enrollment and evaluator isolation acceptance. Require SEMANTIC_DURABLE_TASK_BINDING=PASS, LOCAL_SEMANTIC_TASK_MCP=PASS, LOCAL_SEMANTIC_TASK_RECEIPT=PASS, EVALUATOR_SEALED_ROOT=PASS, LOCAL_EVALUATOR_CONTROL_READBACK=PASS, LOCAL_EVALUATOR_WORKER_DENIAL_MCP=PASS, LOCAL_EVALUATOR_WORKER_DENIAL_RECEIPT=PASS, LOCAL_EVALUATOR_ISOLATION=PASS, EVALUATOR_ISOLATION_ACCEPTANCE=PASS and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS. Do not use older runtime ccdde5c9, do not widen helper/issuer trust, and do not touch PADataset GPUs.

## Remaining work

- In a fresh conversation, confirm workspace_shell_exec exposes candidate-pytest.
- Run candidate-pytest against PADataset Architecture-B PR #23 exact SHA 4f27d00cce9ab15120d924963a5ecf049d032c52 while durable PADataset authority remains befe383fd67c8bca8d8ce370344b33c7e13cd52f.
- Verify the candidate receipt binds durable task checkpoint + candidate SHA/tree and does not mutate authoritative task state.
- Verify ordinary task-bound execution still rejects the same off-checkpoint SHA.
- Then hand execution back to mth602-final-multisurrogate-dqnguard-v1.

## Blockers / gates

- Live semantic authority and live evaluator-isolation acceptance are both prepared but not yet activated on the Lambda host. The first semantic enrollment attempt safely rolled back; the false-negative parser was repaired, and current bundled runtime candidate 6d47e3eca88150c6ad127b6e5901936323fe3ca1 passed Workspace Control #2902.
- Host activation remains a genuine root/operator step because helper/issuer trust is intentionally empty. The transactional upgrade now also provisions a root-owned 0700 evaluator sealed store, proves control write/read/commitment against exact semantic execution source, and proves a fixed hostile-worker denial probe through the existing network-dead bubblewrap sandbox.
- After root activation, ChatGPT must independently verify workspace-semantic-execution-migration-v1 resolves at exact HEAD 74958b5d0d325893fd39045d1e49b5320dca7fa3 and record the live evaluator-isolation acceptance before claim-bearing scored runs are admitted.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
