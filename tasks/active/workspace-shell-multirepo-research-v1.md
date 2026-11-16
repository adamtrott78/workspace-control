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

DO NOT RETRY ROOT ACTIVATION YET. Diagnose and repair the evaluator-denial-probe authorization mismatch exposed by the latest rollback-safe activation attempt. The frozen runtime source workspace-control@6d47e3eca88150c6ad127b6e5901936323fe3ca1 explicitly authorizes profile evaluator-denial-probe for target workspace-control in plugins/workspace-shell/root/job_launcher.py and includes the profile in profiles.v1.json, but the live post-upgrade tools/call returned TARGET_PROFILE_DENIED for that exact target/profile pair. First prove which installed launcher/config/broker component handled the live request and why it did not match 6d47e3…. Make the smallest bounded fix; do not widen to generic shell/root authority and do not touch PADataset GPUs. Validate the exact new runtime head, update the frozen activation tuple, then rerun the transactional upgrader with PADataset befe383fd67c8bca8d8ce370344b33c7e13cd52f, semantic capsule 8019248f6952743d61e90d5abac754356952c18b, and semantic execution 7c20097c5f177f23c16a765b95ce94d7161f0d29. Require all semantic/evaluator acceptance markers plus WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS before proceeding.

## Remaining work

- In a fresh conversation, confirm workspace_shell_exec exposes candidate-pytest.
- Run candidate-pytest against PADataset Architecture-B PR #23 exact SHA 4f27d00cce9ab15120d924963a5ecf049d032c52 while durable PADataset authority remains befe383fd67c8bca8d8ce370344b33c7e13cd52f.
- Verify the candidate receipt binds durable task checkpoint + candidate SHA/tree and does not mutate authoritative task state.
- Verify ordinary task-bound execution still rejects the same off-checkpoint SHA.
- Then hand execution back to mth602-final-multisurrogate-dqnguard-v1.

## Blockers / gates

- LATEST LIVE ACTIVATION FAILED CLOSED AND ROLLED BACK. Operator evidence reached DURABLE_TASK_BINDINGS=PASS, SEMANTIC_DURABLE_TASK_BINDING=PASS, semantic execution materialization at 7c20097c…, EVALUATOR_SEALED_ROOT=PASS, LOCAL_EVALUATOR_CONTROL_READBACK=PASS, RUNTIME_NODE_DEPENDENCIES=PASS, LOCAL_MCP_READY=PASS and LOCAL_MCP_DISCOVERY=PASS; evaluator-denial-probe then failed with TARGET_PROFILE_DENIED for target workspace-control, and the transactional upgrader invoked rollback.
- SOURCE/LIVE DISCREPANCY: validated runtime source 6d47e3eca88150c6ad127b6e5901936323fe3ca1 explicitly permits workspace-control + evaluator-denial-probe in job_launcher.py and defines the profile in profiles.v1.json. Therefore do not redesign the evaluator profile first; determine why the live request was handled by authority/config/runtime state that did not match that frozen source.
- Live activation remains a root/operator gate. Helper and trusted-issuer registries must remain narrow; do not create arbitrary sudo/bash authority as a shortcut.
- After a repaired activation succeeds, ChatGPT must independently verify workspace-semantic-execution-migration-v1 resolves at exact HEAD 7c20097c5f177f23c16a765b95ce94d7161f0d29 and only then run the frozen fake-worker private-route harness.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
