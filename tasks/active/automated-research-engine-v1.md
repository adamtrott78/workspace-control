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
- Checkpoint: 56ca8f608202b6700129a2a54feb74d1d43c9cbf

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: automated-research-engine-v1
- Remote checkpoint: 33339103d1a21842ff7479bd72782ab4dc42f9b9
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: e23da0349160a0a181d356d4f9aee0c0c2ea8b3e
- Remote verified: true

## Next safe action

Merge research-engine PR #1 after its successful PostgreSQL/pgvector CI run, verify research-engine/main, then implement the idempotent curated-corpus PostgreSQL loader and database-backed provenance query regression tests. Continue using PR-triggered CI as the real database runtime.

## Remaining work

- Merge the validated CI documentation PR into research-engine/main and verify main.
- Implement an idempotent PostgreSQL corpus loader for the current curated multi-paper fixture and integration tests.
- Implement database-backed provenance/support/qualifier queries over loaded corpus evidence.
- Add machine-readable schema/fixture validation for research-engine contract fixtures.
- Add provider/parser service interfaces while keeping scientific evidence contracts authoritative.
- Re-run novelty challenge after additional RF-specific papers are loaded; only then consider SUPPORTED_AS_OPEN.
- After implementation vertical-slice tests pass, bulk-ingest the remainder of the already-curated PADataset reference PDFs.

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
