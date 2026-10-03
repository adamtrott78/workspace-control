<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-document-pipeline-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-document-pipeline-v1
- Title: Research Engine Local Document Intelligence and Compute Offload v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Design, benchmark, and integrate a provenance-preserving local document-intelligence pipeline that converts content-addressed research PDFs into reusable LLM-ready paper packages, minimizes paid/plan semantic usage and repeated PDF interpretation, and systematically evaluates every research-engine stage for safe deterministic or local-model offload before production deployment on the Lambda.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 134d60630a1bf16499fee169f28456a670de343f
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: d89d874949570ce8bb593f8ceffb7fd772af3f5f
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 8c875a62d44e91ed91207cdc78d715acb0909346
- Local clean: true

## Next safe action

Keep research-engine-daemon.service inactive/dead and do not START sustained research. Treat research-engine main@d89d874949570ce8bb593f8ceffb7fd772af3f5f as the canonical localization-policy baseline. Begin lambda_production_acceptance by designing and CI-gating a bounded acceptance runner that verifies Lambda checkout/dependencies/runtime caches/shared-inference ownership/authoritative-PDF semantic policy and performs only finite smoke checks with explicit cleanup. The gate must not launch sustained research, must preserve rollback, must not materialize new scientific state, and must leave research-engine-daemon.service inactive/dead unless a deliberately bounded daemon lifecycle check is added with guaranteed stop/cleanup.

## Remaining work

- Design and CI-gate a bounded Lambda production-acceptance runner that verifies canonical checkout, persistent PostgreSQL, parser/runtime/model-cache availability, shared local-inference configuration, authoritative-PDF EXTRACT/VERIFY policy, and operator recovery invariants without starting sustained research.
- Exercise only bounded document-pipeline health/smoke operations required to prove the installed runtimes and shared model owners can initialize and shut down cleanly; preserve daemon rollback and no scientific-state mutation.
- Perform/record CodeFormulaV2 license/deployment review before sustained production enablement.
- Run the bounded Lambda production-acceptance gate and evaluate resource stability, dependency health, process cleanup, and exact configuration.
- If accepted, advance to bounded_production_integration for a rollback-capable production comparison; otherwise fix only the measured deployment defect.

## Blockers / gates

- Lambda local research-engine is last verified clean at main@8c875a62d44e91ed91207cdc78d715acb0909346 while canonical remote main is d89d874949570ce8bb593f8ceffb7fd772af3f5f; fast-forward before production acceptance.
- CodeFormulaV2 deployment/redistribution obligations still require final license/deployment review before sustained production enablement.
- The complete document-pipeline production acceptance gate has not yet been executed on canonical Lambda main.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-document-pipeline-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
