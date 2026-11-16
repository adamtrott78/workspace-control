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
- Remote checkpoint: faf72bfda6a6ce762dd9adde39499af205e6fc69
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: befe383fd67c8bca8d8ce370344b33c7e13cd52f
- Remote verified: true

## Next safe action

Run the validated transactional Workspace Shell upgrade from the exact authority-state branch head produced by this checkpoint, with workspace-control execution candidate faf72bfda6a6ce762dd9adde39499af205e6fc69 and PADataset execution SHA befe383fd67c8bca8d8ce370344b33c7e13cd52f. Require five-service health, LOCAL_MCP_DISCOVERY including candidate-pytest, and a live off-checkpoint candidate-pytest receipt before updating the existing Workspace Shell plugin through Plugin Creator.

## Remaining work

- Deploy the validated host upgrade from the authority-state checkpoint produced after execution candidate faf72bfda6a6ce762dd9adde39499af205e6fc69, explicitly binding PADataset befe383fd67c8bca8d8ce370344b33c7e13cd52f.
- Verify all five Workspace Shell services are active and still boot-disabled, with the job launcher/worker network isolation unchanged.
- Run candidate-pytest against a PADataset candidate SHA that deliberately differs from the durable task checkpoint and verify the receipt binds task_checkpoint_sha + candidate SHA/tree.
- Run a negative candidate test proving ordinary task-bound execution still rejects a mismatched SHA.
- Update the existing private Workspace Shell plugin in place through Plugin Creator and refresh tool discovery.
- Return to PADataset Architecture-B validation using candidate-pytest rather than promoting candidate SHAs into task authority.

## Blockers / gates

- The live Workspace Shell runtime does not yet include candidate-pytest or workspace-shell-candidate-materializer.service; the validated rollback-capable host upgrade must be applied.
- The existing Workspace Shell ChatGPT plugin must be refreshed through Plugin Creator after backend live acceptance so the model-visible schema discovers candidate-pytest.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-multirepo-research-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
