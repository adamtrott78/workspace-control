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

## Next safe action

Populate the newly created private adamtrott78/research-engine repository with the tested 20-file implementation bootstrap, verify exact file hashes/remote checkpoint, register the repository in workspace-control, then continue remotely executable implementation. Run the prepared PostgreSQL/pgvector integration test when a capable runtime becomes available. Do not stop merely because the runtime test is pending while independent safe implementation work remains.

## Remaining work

- Create the dedicated adamtrott78/research-engine implementation repository and initialize it from the validated workspace-control contracts.
- Implement v1 PostgreSQL/pgvector schema and content-addressed artifact-store interfaces.
- Implement fixture/schema validation and load the current five-work corpus as the first test dataset.
- Implement provenance query tests covering Result->Claim support, limitation qualifiers, source locators, and mixed fidelity.
- Promote Broggi 2025 to exact-PDF evidence during later corpus ingestion, not as a blocker for implementation.
- Re-run novelty challenge after additional RF-specific papers are loaded; only then consider SUPPORTED_AS_OPEN.
- After implementation vertical-slice tests pass, bulk-ingest the remainder of the already-curated PADataset reference PDFs.

## Blockers / gates

- PostgreSQL/pgvector integration test remains pending until a capable runtime is confirmed. This does not block remote repository population or further implementation work.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
