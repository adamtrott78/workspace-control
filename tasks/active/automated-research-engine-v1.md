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
- Remote checkpoint: cc4ae9e185257574757ff5da910237a23f4292a1
- Remote verified: true

## Next safe action

On research-engine/main@cc4ae9e185257574757ff5da910237a23f4292a1, add CI that runs the full test suite against a PostgreSQL 18 + pgvector service. Inspect the workflow result and repair any implementation/schema defects without asking for local Docker while GitHub Actions remains a viable runtime surface. Then implement/load the curated corpus and provenance query tests.

## Remaining work

- Add GitHub Actions CI using PostgreSQL 18 + pgvector and run all unit/integration tests on research-engine/main.
- Repair any runtime/schema defect found by CI and rerun until the bootstrap passes on a real PostgreSQL/pgvector instance.
- Implement fixture/schema validation and an idempotent loader for the current curated multi-paper corpus into PostgreSQL.
- Implement provenance query regression tests over loaded corpus evidence and mixed-fidelity state.
- Add provider/parser service interfaces while keeping scientific evidence contracts authoritative.
- Re-run novelty challenge after additional RF-specific papers are loaded; only then consider SUPPORTED_AS_OPEN.
- After implementation vertical-slice tests pass, bulk-ingest the remainder of the already-curated PADataset reference PDFs.

## Blockers / gates

- The initial PostgreSQL integration test has not yet executed against a real PostgreSQL/pgvector runtime; GitHub Actions CI is the next available authorized runtime surface and should be tried before requesting local Docker.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
