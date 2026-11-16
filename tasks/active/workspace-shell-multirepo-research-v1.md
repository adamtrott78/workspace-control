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
- Remote checkpoint: 296d2591b83d86da898940ccc6f6cc5cbcc45374
- Remote verified: true

### PADataset

- Intent: read
- Remote branch: mth602-final-multisurrogate-dqnguard-v1
- Remote checkpoint: befe383fd67c8bca8d8ce370344b33c7e13cd52f
- Remote verified: true

## Next safe action

Apply the transactional Workspace Shell upgrade from the exact authority-state head produced by this checkpoint, using execution candidate 296d2591b83d86da898940ccc6f6cc5cbcc45374 and PADataset befe383fd67c8bca8d8ce370344b33c7e13cd52f. Then prove candidate-pytest live, refresh the existing Workspace Shell plugin through Plugin Creator, and resume STFT from the persistent checkout without rebuilding completed cache files.

## Remaining work

- Deploy the validated host upgrade from the authority-state checkpoint produced after execution candidate 296d2591b83d86da898940ccc6f6cc5cbcc45374, explicitly binding PADataset befe383fd67c8bca8d8ce370344b33c7e13cd52f.
- Verify five-service live health and candidate-pytest discovery.
- Run an off-checkpoint candidate-pytest receipt to prove candidate SHA execution without mutating durable task authority.
- Refresh the existing private Workspace Shell plugin in place through Plugin Creator.
- Resume the STFT ablation from persistent checkout head 6fa2ef479d4a05de339154bfaed7a57648339c1b; completed cache files must be skipped, not rebuilt.

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
