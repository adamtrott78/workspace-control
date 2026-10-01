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

## Recovery restore point

- Identity: ac04cf29c0a1174b7b570d501c534d6798815d47
- stage=vertical_slice_validation
- last_validated_boundary=research-engine/main@ac04cf29c0a1174b7b570d501c534d6798815d47 (PR #4 checkpointed novelty persistence; PostgreSQL/pgvector CI PASS)
- external_runtime_prepared=research-engine/acquire-rf-counterevidence commit 1009e230a22878ad9ab54ff2a37ae1c8353b7043 prepared from ac04cf29c0a1174b7b570d501c534d6798815d47; branch ref not yet advanced at restore-point creation
- purpose=acquire exact arXiv v1 PDFs for 2605.15593 and 2606.12718, verify SHA-256/PDF magic/page count, and upload exact-source bundle
- resume=verify acquire-rf-counterevidence ref; if it points to 1009e230a22878ad9ab54ff2a37ae1c8353b7043 inspect newest Acquire RF novelty counterevidence run/artifact; if not, advance it non-force to prepared commit

## Next safe action

Launch prepared exact arXiv acquisition by non-force advancing research-engine/acquire-rf-counterevidence to 1009e230a22878ad9ab54ff2a37ae1c8353b7043. Then inspect/download the resulting GitHub Actions artifact, verify exact bytes, parse the two PDFs, ingest them into the corpus/evidence model, create a new knowledge checkpoint, and re-run persisted novelty challenges.

## Remaining work

- Acquire exact arXiv source artifacts for the 2026 dynamic/open-set RF paper and the 2026 RF OOD-detector paper that challenged the pilot gaps.
- Extract and ingest those papers as first-class corpus/evidence members, then create a new knowledge checkpoint and re-run novelty challenges against corpus-backed evidence instead of abstract-only external metadata.
- Promote Broggi 2025 to exact-PDF evidence from the user's local PADataset copy only when that non-blocking local-byte boundary becomes the next necessary step.
- Continue expanding RF-specific open-set/OOD literature until novelty challenge results are stable enough for human research-direction review.
- After exact-source scaling passes, bulk-ingest the remainder of the already-curated PADataset reference PDFs.

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
