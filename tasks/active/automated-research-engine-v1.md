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
- Remote checkpoint: f9e2a519b5bcde1c2c5a76579bed695f454658a8
- Remote verified: true

## Next safe action

Continue vertical_slice_validation from automated-research-engine-v1@f9e2a519b5bcde1c2c5a76579bed695f454658a8. Use the demonstrated five-work object/graph/query requirements to choose and document the v1 persistence/index architecture. Preserve immutable evidence/source records as authority and treat graph/vector indexes as rebuildable projections. Then prepare a bounded exact-PDF promotion check for 2-3 PADataset local reference PDFs to measure OCR-vs-PDF extraction fidelity.

## Remaining work

- Select and document the v1 persistence/index architecture based on demonstrated requirements: immutable source/artifact identity, typed relational records, directed evidence relations, recursive provenance queries, JSON-like extensibility, full-text retrieval, and optional semantic retrieval.
- Mechanically validate representative fixtures against their JSON schemas in the future implementation repository.
- Promote a small subset of PADataset OCR_DERIVED works to exact-PDF-verified artifacts by hashing/parsing their local PDFs, then compare OCR-derived extraction against exact-PDF extraction to measure locator/fidelity error.
- Re-run novelty challenge after additional RF-specific papers are ingested; only then consider whether any candidate can move toward SUPPORTED_AS_OPEN.
- Create the dedicated research-engine implementation repository when a supported repository-creation path is available; move executable provider/parser/storage code there while retaining workspace-control as control plane.
- After the vertical slice passes exact-PDF fidelity checks, bulk-ingest the remainder of the already-curated PADataset reference PDFs through the same pipeline.

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
