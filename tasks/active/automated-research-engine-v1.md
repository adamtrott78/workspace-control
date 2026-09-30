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
- Remote checkpoint: 24e62c9165b155cda23763dcf1d97b14d923b2b9
- Remote verified: true

## Next safe action

Run the bounded local exact-PDF promotion bundle for the three PADataset files 2013_scheirer_toward_open_set_recognition.pdf, 2020_liu_energy_ood_detection.pdf, and 2024_baye_varmax_milcom.pdf at their manifest-recorded local paths. Emit SHA-256, byte length, PDF magic/page count, and package exact copies into one temporary tar.gz for upload to the extraction executor. Do not modify PADataset.

## Remaining work

- Promote three PADataset OCR_DERIVED reference works (Scheirer 2013, Liu 2020, Baye 2024) to exact-PDF-verified artifacts by hashing the local PDFs and making those exact bytes available to the extraction executor.
- For each promoted paper, parse exact PDF layout and compare selected OCR-derived evidence anchors against exact-PDF extraction to quantify locator/text fidelity.
- Mechanically validate representative fixtures against their JSON schemas in the dedicated implementation repository.
- Re-run cross-paper synthesis/novelty challenge using exact-PDF evidence for the promoted subset and additional RF-specific papers.
- Create the dedicated research-engine implementation repository when a supported repository-creation path is available; implement PostgreSQL/artifact-store/provider/parser services there.
- After exact-PDF fidelity checks pass, bulk-ingest the remainder of the already-curated PADataset reference PDFs through the same pipeline.

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
