<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/research-engine-local-extract-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: research-engine-local-extract-redesign-v1
- Title: Research Engine Mostly-Local EXTRACT Redesign v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Return to first principles on research-engine EXTRACT and identify, benchmark, and if justified implement a provenance-preserving mostly-local extraction architecture that makes STANDARD Codex a rare ambiguity/failure fallback rather than the default, while reusing accepted local document/VERIFY infrastructure and not repeating approaches already invalidated by durable evidence.

## Parent execution owner

research-engine-local-document-pipeline-v1

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 796dd9fb9c5fd25009d756a4fd42d53b85a5ac3d
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: main
- Remote checkpoint: 5f6eec7b629b4746117f2f0a74d4531c642f8025
- Remote verified: true
- Local path: /home/atrott/adamArchives/Adam/research-engine
- Local branch: main
- Local HEAD: 5f6eec7b629b4746117f2f0a74d4531c642f8025
- Local clean: true

## Current stage

problem_reframe_and_external_solution_survey

## Next safe action

Conduct a current external research survey of mostly-local scientific/document EXTRACT architectures and implementations, explicitly comparing architectural decomposition rather than simply trying another general local chat model. Reuse the accepted document/provenance pipeline as substrate, exclude previously failed approaches as-is, and checkpoint a shortlist plus benchmark/fallback hypotheses before any new heavyweight model download or Lambda bakeoff.

## Remaining work

- Survey current research and open-source systems for local scientific structured extraction, evidence-first claim extraction, schema-guided IE, retrieval/reranking, extractive QA, NLI/verification, and confidence-gated remote fallback.
- Build a reuse/exclusion matrix from the parent evidence so already-failed approaches are not reintroduced under new names.
- Select a small set of materially distinct architectures that can run on the current Lambda hardware.
- Define a benchmark/fallback contract before downloading or integrating new heavyweight models.

## Blockers / gates

- None recorded at task creation.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/research-engine-local-extract-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the complete handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
