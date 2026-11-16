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

FINAL ROOT ACTIVATION TUPLE IS FROZEN. From the exact authority-state head produced by this checkpoint, run plugins/workspace-shell/install/upgrade_multirepo_padataset_v1.sh with workspace-control runtime candidate 6d47e3eca88150c6ad127b6e5901936323fe3ca1, PADataset execution befe383fd67c8bca8d8ce370344b33c7e13cd52f, semantic capsule source 8019248f6952743d61e90d5abac754356952c18b, and semantic execution binding 7c20097c5f177f23c16a765b95ce94d7161f0d29. Semantic execution is intentionally frozen: 7c20097c passed #2904/#226/#504 and capsule/state 8019248f passed #2907/#229/#507. Runtime 6d47e3ec passed #2902 and bundles semantic authority enrollment plus evaluator sealed-store control-readback and fixed hostile-worker denial acceptance. Require SEMANTIC_DURABLE_TASK_BINDING=PASS, LOCAL_SEMANTIC_TASK_MCP=PASS, LOCAL_SEMANTIC_TASK_RECEIPT=PASS, EVALUATOR_SEALED_ROOT=PASS, LOCAL_EVALUATOR_CONTROL_READBACK=PASS, LOCAL_EVALUATOR_WORKER_DENIAL_MCP=PASS, LOCAL_EVALUATOR_WORKER_DENIAL_RECEIPT=PASS, LOCAL_EVALUATOR_ISOLATION=PASS, EVALUATOR_ISOLATION_ACCEPTANCE=PASS and WORKSPACE_SHELL_MULTIREPO_UPGRADE=PASS. Do not substitute older semantic SHAs, widen helper/issuer trust, or touch PADataset GPUs. After activation ChatGPT independently verifies exact semantic HEAD 7c20097c… and proceeds directly to the reviewed-private-route fake-worker harness.

## Remaining work

- In a fresh conversation, confirm workspace_shell_exec exposes candidate-pytest.
- Run candidate-pytest against PADataset Architecture-B PR #23 exact SHA 4f27d00cce9ab15120d924963a5ecf049d032c52 while durable PADataset authority remains befe383fd67c8bca8d8ce370344b33c7e13cd52f.
- Verify the candidate receipt binds durable task checkpoint + candidate SHA/tree and does not mutate authoritative task state.
- Verify ordinary task-bound execution still rejects the same off-checkpoint SHA.
- Then hand execution back to mth602-final-multisurrogate-dqnguard-v1.

## Blockers / gates

- The repository side is complete for the next maintenance window: Workspace Shell runtime 6d47e3eca88150c6ad127b6e5901936323fe3ca1 is validated (#2902), semantic execution 7c20097c5f177f23c16a765b95ce94d7161f0d29 is 3/3 green (#2904/#226/#504), and semantic capsule/state 8019248f6952743d61e90d5abac754356952c18b is 3/3 green (#2907/#229/#507).
- Live activation remains a genuine root/operator gate because privileged helper and trusted issuer registries intentionally remain empty. No ChatGPT-side tool is authorized to sudo or mutate the host root state.
- After activation, ChatGPT must independently verify the semantic task resolves at exact HEAD 7c20097c5f177f23c16a765b95ce94d7161f0d29 and record the bundled evaluator-isolation acceptance before any claim-bearing scored run. Then run the frozen fake-worker transport harness through the reviewed private route before real-account use.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
