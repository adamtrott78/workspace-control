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
- Remote checkpoint: 54ac65cbcd4211554710b8f8f4231c6c9554e3cc
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: befe383fd67c8bca8d8ce370344b33c7e13cd52f
- Remote verified: true

## Next safe action

After this control-cycle state validates, retry the transactional root activation using the exact authority-state commit produced here and runtime 54ac65cbcd4211554710b8f8f4231c6c9554e3cc (#2942 SUCCESS), with the unchanged PADataset/semantic tuple. Require LOCAL_CANDIDATE_MATERIALIZER_READY=PASS before semantic MCP acceptance, then LOCAL_SEMANTIC_TASK_RECEIPT=PASS, LOCAL_EVALUATOR_WORKER_DENIAL_RECEIPT=PASS, LOCAL_EVALUATOR_ISOLATION=PASS, EVALUATOR_ISOLATION_ACCEPTANCE=PASS, and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS. Roll back on any failure.

## Remaining work

- Retry transactional root activation from the exact authority-state commit produced by this control cycle using runtime 54ac65cbcd4211554710b8f8f4231c6c9554e3cc and the unchanged PADataset/semantic tuple.
- Require LOCAL_CANDIDATE_MATERIALIZER_READY=PASS before semantic MCP acceptance, then all semantic/evaluator receipt and isolation markers plus WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS.
- After PASS, independently verify live Workspace Shell runtime and semantic execution 7c20097c5f177f23c16a765b95ce94d7161f0d29, record evaluator-isolation acceptance, sync umbrella state, and continue to the reviewed fake-worker route.

## Blockers / gates

- Runtime 54ac65cbcd4211554710b8f8f4231c6c9554e3cc is repository-validated but not live. The ninth activation remains rolled back.
- The ninth retry failed because the upgrade path omitted worker_gid from candidate-materializer.json, causing the newly hardened materializer to fail closed and leave its socket unavailable.
- Runtime 54ac65cb… fixes the upgrade-time config omission and adds an explicit materializer responsiveness gate before semantic MCP execution.
- Live activation remains an operator/root gate. Full success still requires materializer readiness, semantic receipt PASS, evaluator worker-denial receipt PASS, evaluator isolation acceptance PASS, and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS.
- After activation succeeds, independently verify live runtime and frozen semantic execution before fake-worker transport execution.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
