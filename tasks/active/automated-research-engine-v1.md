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
- Remote checkpoint: 1c32bde9e57772e81bb6eb6898d6cbd817ddbf87
- Remote verified: true

## Next safe action

Continue extraction_pipeline using the exact SourceArtifact for arXiv 2108.13099v1 (SHA-256 7fcfc9929fd80a94095657ebf644be3301000d0a4342b74de1adc2af529ff7ab). Build a normalized document/source-locator representation and a first typed evidence fixture for the paper. Preserve exact source locations and distinguish source-derived statements from inference. Do not choose the persistence database yet.

## Remaining work

- Parse the first acquired source into a normalized document representation with stable source locators.
- Extract and validate typed scientific evidence from arXiv 2108.13099v1: research question, method, experiment, dataset/population, metric, result, claim, and limitation where present.
- Create a manually checked benchmark annotation for the first paper and compare automated extraction against it.
- Extend extraction to several additional deep-read pilot papers to test schema generality.
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
