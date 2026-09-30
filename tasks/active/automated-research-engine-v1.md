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
- Remote checkpoint: b1734cea1498d2206902c115e4224fffc824aa09
- Remote verified: true

## Next safe action

Continue on automated-research-engine-v1 by defining the evidence contract in architecture/automated-research-engine-v1.md: specify canonical Work, SourceArtifact, SourceLocator, EvidenceObject, Claim, Method, Experiment, Dataset/Population, Metric, Result, Limitation, Inference, and EvidenceRelation records plus their required provenance and verification fields. Do not choose a database yet.

## Remaining work

- Define the canonical evidence/provenance contract before selecting persistence technology.
- Define the reproducible corpus/search-run record and canonical work/version identity model.
- Prototype multi-provider discovery and lawful full-text acquisition adapters.
- Build normalized parsing and typed evidence extraction with source locators and verification state.
- Choose persistence/indexing architecture only after the evidence contract is stable enough to evaluate storage requirements.
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
