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
- Checkpoint: 2ee1f6584178df68d1f01a219fb526d4745707bf

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: automated-research-engine-v1
- Remote checkpoint: 33339103d1a21842ff7479bd72782ab4dc42f9b9
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: de1d1a0ca0f649895d461e40a1496071443e32d7
- Remote verified: true

## Recovery restore point

- Identity: de1d1a0ca0f649895d461e40a1496071443e32d7
- stage=vertical_slice_validation
- last_validated_boundary=research-engine/main@de1d1a0ca0f649895d461e40a1496071443e32d7 (immutable evidence history + deterministic knowledge checkpoints; PostgreSQL/pgvector CI PASS)
- external_runtime_prepared=research-engine/acquire-broggi-source commit 115335b26852df2af840191a713ffe481f759947 prepared from 10ce97b9157d745c6e437983fb02e2e9e8ae72c5; branch ref not yet advanced at restore-point creation
- purpose=resolve HICSS Broggi 2025 exact PDF via ScholarSpace handle 10125/109750 / DSpace APIs after AISel returned HTTP 403
- resume=verify acquire-broggi-source ref; if it points to 115335b26852df2af840191a713ffe481f759947 inspect the newest Acquire Broggi 2025 exact source Actions run and artifact; if ref has not advanced, advance it non-force to that prepared commit

## Next safe action

Launch the prepared Broggi ScholarSpace acquisition by non-force advancing research-engine/acquire-broggi-source from 10ce97b9157d745c6e437983fb02e2e9e8ae72c5 to 115335b26852df2af840191a713ffe481f759947. Then inspect the resulting GitHub Actions run/artifact. Continue independent novelty-persistence work while external acquisition runs; do not stop solely to poll.

## Remaining work

- Promote Broggi 2025 from OCR_DERIVED to exact-PDF evidence if an authorized scholarly/direct source can provide exact bytes; otherwise use the existing local PADataset PDF only when a true local-byte boundary is reached.
- Ingest additional RF-specific open-set/OOD papers into the implementation database and re-run adversarial novelty challenge over a broader corpus.
- Implement novelty-challenge persistence/query services in research-engine using knowledge checkpoints so prior-work rejection/narrowing is reproducible.
- Only after broader exact-source corpus validation consider any GapCandidate eligible for SUPPORTED_AS_OPEN.
- After the scaling slice passes, bulk-ingest the remainder of the already-curated PADataset reference PDFs.

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
