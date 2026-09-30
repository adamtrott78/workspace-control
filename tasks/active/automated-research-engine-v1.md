<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/automated-research-engine-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: automated-research-engine-v1
- Title: Automated research engine v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Design and prove a provenance-preserving automated research engine that turns scholarly literature into structured evidence, durable knowledge, challenged research gaps, fundable research programs, and workspace-control-executable research projects.

## Workflow

- Repository: workspace-control
- Path: policies/OPERATOR_WORKFLOW.md
- Checkpoint: 03a51fdbe2a9153f2b5e45054eec6e927a9dda36

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: automated-research-engine-v1
- Remote checkpoint: d2baadf2c20f20a1edd958fef4f041706e34115f
- Remote verified: true

## Next safe action

Vertical-slice validation is active at automated-research-engine-v1@d2baadf2c20f20a1edd958fef4f041706e34115f. The end-to-end control/data contracts have been proven on one exact full-text paper. Next, ingest a small multi-paper RF OSR corpus through the same pipeline—prefer the user's already-curated cited-paper PDFs in PADataset once their exact route is resolved—then validate cross-paper synthesis, contradiction/novelty behavior, and extraction fidelity before bulk-ingesting the remainder.

## Remaining work

- Run vertical-slice validation across multiple additional RF OSR papers so cross-paper identity, evidence, contradiction, synthesis, and novelty behavior are tested rather than only single-paper mechanics.
- Use the user's already-curated/cited PDFs in PADataset as the first serious RF OSR corpus once their exact project route is resolved; ingest them through the same acquisition/evidence pipeline without special-casing.
- Measure extraction/source-locator fidelity on a manually checked sample and track unsupported-extraction rate.
- Re-run novelty challenge after the multi-paper corpus is indexed; only then consider whether any candidate can move toward SUPPORTED_AS_OPEN.
- Choose persistence/indexing architecture based on observed graph/query/corpus scale requirements.
- Create the dedicated research-engine implementation repository when a supported repository-creation path is available; move executable provider/parser/storage code there while retaining workspace-control as control plane.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
