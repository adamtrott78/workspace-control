<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/automated-research-engine-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: automated-research-engine-v1
- Title: Automated research engine v1
- Status: BLOCKED_RUNTIME
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
- Remote checkpoint: 56533236666d17e742c96528807ced11dbc3b92d
- Remote verified: true

## Next safe action

Run architecture/research-engine/exact-pdf-promotion-protocol-v1.md's noninteractive local command against the manifest-recorded PADataset checkout. Return the printed receipt and upload /tmp/research-engine-pdf-promotion.tar.gz. Do not modify PADataset. After receipt/upload, verify the bundle and resume vertical_slice_validation with exact-PDF parsing and OCR-fidelity comparison.

## Remaining work

- Promote three PADataset OCR_DERIVED reference works (Scheirer 2013, Liu 2020, Baye 2024) to exact-PDF-verified artifacts by hashing the local PDFs and making those exact bytes available to the extraction executor.
- For each promoted paper, parse exact PDF layout and compare selected OCR-derived evidence anchors against exact-PDF extraction to quantify locator/text fidelity.
- Mechanically validate representative fixtures against their JSON schemas in the dedicated implementation repository.
- Re-run cross-paper synthesis/novelty challenge using exact-PDF evidence for the promoted subset and additional RF-specific papers.
- Create the dedicated research-engine implementation repository when a supported repository-creation path is available; implement PostgreSQL/artifact-store/provider/parser services there.
- After exact-PDF fidelity checks pass, bulk-ingest the remainder of the already-curated PADataset reference PDFs through the same pipeline.

## Blockers / gates

- Exact source PDFs for the next fidelity test are local-only in the PADataset checkout and are not available to this executor. A bounded read-only local bundle is required for Scheirer 2013, Liu 2020, and Baye 2024.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
