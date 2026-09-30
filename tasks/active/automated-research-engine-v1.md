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
- Remote checkpoint: d0e5f8e652081f531b51b1518795f9b1628b2696
- Remote verified: true

## Next safe action

Continue evidence_graph from automated-research-engine-v1@d0e5f8e652081f531b51b1518795f9b1628b2696. Define the storage-agnostic graph projection and query contract using the first full-text fixture. Prove that a query can traverse from the paper's conclusion claim to supporting/qualifying result/method evidence and back to exact PDF page/bbox locators. Do not select the database yet.

## Remaining work

- Define the durable evidence-graph projection from Work/WorkVersion, evidence objects, locators, and EvidenceRelation records without losing source-specific context.
- Build graph queries that can answer which source results support/qualify/contradict a claim and return exact source locators.
- Test graph projection and retrieval against the first full-text paper fixture.
- Extend extraction to several additional deep-read pilot papers during vertical-slice validation to test schema generality and cross-paper relations.
- Choose persistence/indexing architecture only after graph/query requirements are demonstrated against real evidence objects.
- Build provenance-preserving synthesis, contradiction handling, gap generation, and adversarial novelty challenge.
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
