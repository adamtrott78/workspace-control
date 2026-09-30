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
- Remote checkpoint: 7f09a557240722b4d104cbb7d7a2d99779974755
- Remote verified: true

## Next safe action

Create the dedicated research-engine implementation repository from the validated contracts at automated-research-engine-v1@7f09a557240722b4d104cbb7d7a2d99779974755. Initialize PostgreSQL/pgvector schema, content-addressed artifact-store interface, contract/fixture validator, and first five-work corpus load/query tests. Continue through remotely executable implementation work; suspend only at a demonstrated runtime/human-decision/authority boundary per policies/OPERATOR_WORKFLOW.md.

## Remaining work

- Create the dedicated adamtrott78/research-engine implementation repository and initialize it from the validated workspace-control contracts.
- Implement v1 PostgreSQL/pgvector schema and content-addressed artifact-store interfaces.
- Implement fixture/schema validation and load the current five-work corpus as the first test dataset.
- Implement provenance query tests covering Result->Claim support, limitation qualifiers, source locators, and mixed fidelity.
- Promote Broggi 2025 to exact-PDF evidence during later corpus ingestion, not as a blocker for implementation.
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
