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
- Remote checkpoint: fc79aaaecbb83e1cf63f048449a6a999a0b57530
- Remote verified: true

## Next safe action

Continue ingress_prototype at automated-research-engine-v1@fc79aaaecbb83e1cf63f048449a6a999a0b57530. First implement/validate canonical Work and WorkVersion resolution for the pilot's known duplicate/version cases, then obtain bytes and a cryptographic hash for at least one lawful OA source using a capable executor. Do not collapse source resolution and acquisition into one state, and do not choose the persistence database yet.

## Remaining work

- Implement canonical Work/WorkVersion identity resolution against the pilot duplicate/version cases.
- Acquire and content-hash at least one lawful full-text source artifact using an executor/tool path that can retrieve bytes; preserve failed attempts separately.
- Define and test explicit CorpusDecision screening records on the RF pilot.
- Build normalized parsing and typed evidence extraction with source locators and verification state.
- Choose persistence/indexing architecture only after real ingress/extraction objects demonstrate storage/query requirements.
- Build provenance-preserving synthesis, contradiction handling, gap generation, and adversarial novelty challenge.
- Build the research-program/funding/proposal layer and explicit human gates.
- Bridge an approved research program into a workspace-control project execution workflow.
- Run the narrow-domain vertical slice and measure evidence fidelity, traceability, novelty false-positive rate, and execution handoff quality.

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
