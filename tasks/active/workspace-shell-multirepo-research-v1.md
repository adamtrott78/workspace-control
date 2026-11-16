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
- Remote checkpoint: df24022f897643282b4ce16aa727fa2dd646f859
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: befe383fd67c8bca8d8ce370344b33c7e13cd52f
- Remote verified: true

## Next safe action

After this control-cycle state validates, retry the transactional root activation using the exact authority-state commit produced here and runtime df24022f897643282b4ce16aa727fa2dd646f859 (#2939 SUCCESS), with PADataset befe383fd67c8bca8d8ce370344b33c7e13cd52f, semantic capsule 8019248f6952743d61e90d5abac754356952c18b, and semantic execution 7c20097c5f177f23c16a765b95ce94d7161f0d29. The exact-source materializer now binds source contents to the hostile worker group without world-readable repo contents and rematerializes stale root-private caches. Require LOCAL_SEMANTIC_TASK_RECEIPT=PASS, LOCAL_EVALUATOR_WORKER_DENIAL_RECEIPT=PASS, LOCAL_EVALUATOR_ISOLATION=PASS, EVALUATOR_ISOLATION_ACCEPTANCE=PASS, and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS. Roll back on any failure.

## Remaining work

- Retry transactional root activation from the exact authority-state commit produced by this control cycle using runtime df24022f897643282b4ce16aa727fa2dd646f859 and the unchanged PADataset/semantic tuple.
- Require semantic/evaluator receipt and isolation PASS plus WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS; rollback on any failure.
- After PASS, independently verify live Workspace Shell runtime and semantic execution 7c20097c5f177f23c16a765b95ce94d7161f0d29, record evaluator-isolation acceptance, sync umbrella state, then derive and run the reviewed account-free fake-worker route.

## Blockers / gates

- Runtime df24022f897643282b4ce16aa727fa2dd646f859 is repository-validated but not live. The eighth activation remains rolled back.
- The eighth retry passed authorization and all SHA/source-mode checks but sandboxed git-read exited 128. Exact stderr content was not recovered.
- Repository source inspection demonstrated that root materialization under UMask=0077 previously left nested Git metadata potentially root-private to the hostile worker. Runtime df24022f… repairs worker readability at the materialization substrate while keeping repo contents non-world-readable.
- Live activation remains an operator/root gate. Full success still requires LOCAL_SEMANTIC_TASK_RECEIPT=PASS, evaluator worker-denial receipt PASS, evaluator isolation acceptance PASS, and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS.
- After activation succeeds, independently verify live runtime and frozen semantic execution before any fake-worker transport execution.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
