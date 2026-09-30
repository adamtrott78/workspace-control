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
- Remote checkpoint: 33339103d1a21842ff7479bd72782ab4dc42f9b9
- Remote verified: true

## Next safe action

Human local action is now genuinely required. Create an empty private GitHub repository named adamtrott78/research-engine using the local authenticated gh CLI, and report docker/docker compose availability. Do not initialize files in the repo. After the repo exists, ChatGPT should populate the tested 20-file bootstrap directly through GitHub and then run the prepared PostgreSQL integration test on a capable local runtime. Human-transfer scratch root is ~/adamArchives/Adam/.workspace-control/tmp (or WORKSPACE_CONTROL_SCRATCH_ROOT).

## Remaining work

- Create the dedicated adamtrott78/research-engine implementation repository and initialize it from the validated workspace-control contracts.
- Implement v1 PostgreSQL/pgvector schema and content-addressed artifact-store interfaces.
- Implement fixture/schema validation and load the current five-work corpus as the first test dataset.
- Implement provenance query tests covering Result->Claim support, limitation qualifiers, source locators, and mixed fidelity.
- Promote Broggi 2025 to exact-PDF evidence during later corpus ingestion, not as a blocker for implementation.
- Re-run novelty challenge after additional RF-specific papers are loaded; only then consider SUPPORTED_AS_OPEN.
- After implementation vertical-slice tests pass, bulk-ingest the remainder of the already-curated PADataset reference PDFs.

## Blockers / gates

- Connected GitHub tooling can mutate existing repositories but exposes no repository-creation operation; the required adamtrott78/research-engine repository does not yet exist.
- The tested implementation includes a real PostgreSQL/pgvector integration test, but the current executor has neither Docker nor a PostgreSQL server/psql runtime.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
