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
- Remote checkpoint: 9984c3d68e01bbaea6dafe6dc941df82d1184ced
- Remote verified: true

## Next safe action

Continue synthesis_gap_engine from automated-research-engine-v1@9984c3d68e01bbaea6dafe6dc941df82d1184ced. Define SynthesisArtifact and GapCandidate contracts. Build a one-paper synthesis only as a scoped machinery test, clearly labeling its evidence boundary. Then generate one or more candidate gap hypotheses and adversarially search current literature for prior work that could invalidate them; do not mark any RF OSR gap SUPPORTED_AS_OPEN until additional papers are ingested.

## Remaining work

- Define reproducible SynthesisArtifact and GapCandidate projection/query contracts over evidence-graph snapshots.
- Generate a first synthesis from the one-paper graph while explicitly declaring that its evidence scope is one work and is insufficient for field-level conclusions.
- Generate candidate gap signals only as hypotheses/inferences, then run adversarial novelty searches intended to disprove them.
- Ingest additional pilot papers before accepting any field-level RF OSR gap as SUPPORTED_AS_OPEN.
- Choose persistence/indexing architecture only after graph/synthesis/query requirements are demonstrated against real evidence objects.
- Build the research-program/funding/proposal layer and explicit human gates.
- Bridge an approved research program into a workspace-control project execution workflow.
- After the end-to-end pipeline is validated, bootstrap the first real RF OSR knowledge corpus from the PDFs already curated/cited in the user's research paper and stored in PADataset's paper area; resolve the exact PADataset route at that time and ingest them through the same provenance-preserving pipeline rather than special-casing them.

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
