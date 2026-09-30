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
- Remote checkpoint: 6b33ababe9e58de33941c8ad2d3161c02551ce7e
- Remote verified: true

## Next safe action

Continue directly in adamtrott78/research-engine from main@6b33ababe9e58de33941c8ad2d3161c02551ce7e. Enforce immutable evidence/relation identity with explicit supersession/history, then add deterministic knowledge checkpoints and PostgreSQL regression tests. Use PR-triggered GitHub Actions as the real PostgreSQL/pgvector runtime. Continue until a genuine capability, authority, or required-human-decision boundary is reached.

## Remaining work

- Enforce immutable authoritative evidence/relation IDs: identical re-entry is idempotent, but semantic changes under the same ID must be rejected and represented by superseding records/events.
- Implement deterministic knowledge checkpoints so syntheses bind to a reproducible corpus/evidence state rather than live database contents.
- Add database regression tests for supersession/history and deterministic checkpoint reproduction.
- Promote Broggi 2025 to exact-PDF evidence during corpus scaling; this is not a blocker for implementation hardening.
- Ingest additional RF-specific papers and re-run novelty challenge before any GapCandidate can move toward SUPPORTED_AS_OPEN.
- After hardening tests pass, bulk-ingest the remainder of the already-curated PADataset reference PDFs.

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
