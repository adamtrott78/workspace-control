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
- Remote checkpoint: 2c2087d0a7be2ed897598cab4a95e364e2b528f7
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: befe383fd67c8bca8d8ce370344b33c7e13cd52f
- Remote verified: true

## Next safe action

After this JSON+Markdown control-cycle state passes exact-head validation and handoff checks, retry the transactional activation using the exact authority-state commit, runtime 2c2087d0a7be2ed897598cab4a95e364e2b528f7 (#2914 SUCCESS), PADataset befe383fd67c8bca8d8ce370344b33c7e13cd52f, semantic capsule 8019248f6952743d61e90d5abac754356952c18b, and semantic execution 7c20097c5f177f23c16a765b95ce94d7161f0d29. Require SEMANTIC_DURABLE_TASK_BINDING=PASS, LOCAL_SEMANTIC_TASK_MCP=PASS, LOCAL_SEMANTIC_TASK_RECEIPT=PASS, EVALUATOR_SEALED_ROOT=PASS, LOCAL_EVALUATOR_CONTROL_READBACK=PASS, LOCAL_EVALUATOR_WORKER_DENIAL_MCP=PASS, LOCAL_EVALUATOR_WORKER_DENIAL_RECEIPT=PASS, LOCAL_EVALUATOR_ISOLATION=PASS, EVALUATOR_ISOLATION_ACCEPTANCE=PASS, and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS. Roll back on any failure. After PASS, independently verify semantic HEAD 7c20097c… and proceed to the frozen fake-worker private-route harness.

## Remaining work

- Retry the transactional activation from the exact authority-state commit produced by this control cycle using runtime 2c2087d0a7be2ed897598cab4a95e364e2b528f7, PADataset befe383fd67c8bca8d8ce370344b33c7e13cd52f, semantic capsule 8019248f6952743d61e90d5abac754356952c18b, and semantic execution 7c20097c5f177f23c16a765b95ce94d7161f0d29.
- Require all existing semantic/evaluator acceptance markers and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS; rollback remains mandatory on any failure.
- After activation PASS, verify the live semantic task at exact execution HEAD 7c20097c5f177f23c16a765b95ce94d7161f0d29 and record evaluator-isolation acceptance before returning to the integrated semantic program.

## Blockers / gates

- Repaired runtime 2c2087d0a7be2ed897598cab4a95e364e2b528f7 is repository-validated but not live. The prior activation remains rolled back.
- Live activation remains an operator gate. Success requires the existing semantic/evaluator acceptance markers and rollback on any failure.
- Existing helper, issuer, target/profile, network, evaluator-path, PADataset, and GPU authority boundaries remain unchanged.
- After activation succeeds, independently verify workspace-semantic-execution-migration-v1 at exact HEAD 7c20097c5f177f23c16a765b95ce94d7161f0d29 before the frozen fake-worker private-route harness.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
