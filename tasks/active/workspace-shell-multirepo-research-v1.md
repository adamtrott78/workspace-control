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

## Next safe action

After this control-cycle state validates, retry the transactional root activation using the exact authority-state commit produced here and runtime 79e8940589d0ac448d40fd2a1560a4e59e817c73 (#2934 SUCCESS), with the frozen PADataset/semantic tuple. The semantic git-read request now obeys its unchanged 30000 ms ceiling. Require LOCAL_SEMANTIC_TASK_RECEIPT=PASS, LOCAL_EVALUATOR_WORKER_DENIAL_RECEIPT=PASS, LOCAL_EVALUATOR_ISOLATION=PASS, EVALUATOR_ISOLATION_ACCEPTANCE=PASS, and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS. Roll back on any failure.

## Remaining work

- Retry transactional root activation from the new exact authority-state commit using runtime 79e8940589d0ac448d40fd2a1560a4e59e817c73, PADataset befe383fd67c8bca8d8ce370344b33c7e13cd52f, semantic capsule 8019248f6952743d61e90d5abac754356952c18b, and semantic execution 7c20097c5f177f23c16a765b95ce94d7161f0d29.
- Require all semantic/evaluator receipt and isolation markers plus WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS; rollback on any failure.
- After PASS, independently verify live runtime and semantic execution, record evaluator-isolation acceptance, sync umbrella state, then derive and run the reviewed private fake-worker route.

## Blockers / gates

- Runtime 79e8940589d0ac448d40fd2a1560a4e59e817c73 is repository-validated but not live. The seventh activation remains rolled back.
- The seventh retry produced a definitive semantic rejection: TIMEOUT_DENIED because the caller requested 50000 ms for git-read while the frozen profile ceiling is 30000 ms.
- Runtime 79e89405… corrects the caller to 30000 ms and does not change the frozen policy ceiling or any execution authority.
- Live activation remains an operator/root gate. Full success still requires semantic receipt PASS, evaluator worker-denial receipt PASS, evaluator isolation acceptance PASS, and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS.
- After activation succeeds, independently verify live runtime and semantic execution 7c20097c5f177f23c16a765b95ce94d7161f0d29 before the frozen fake-worker route.
