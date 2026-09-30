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
- Remote checkpoint: a77f39d566492ff56875644256095abb8366359e
- Remote verified: true

## Next safe action

Continue execution_bridge from automated-research-engine-v1@a77f39d566492ff56875644256095abb8366359e. Define the approval-gated mapping from ResearchProgram to workspace-control task/workflow state. Use the current DRAFT_NOT_APPROVED pilot only to prove that the bridge refuses to instantiate a project. Define the exact payload that would become executable after APPROVED state; do not create a research project or infer approval.

## Remaining work

- Define the execution-bridge contract that maps an APPROVED ResearchProgram into a workspace-control task/workflow without reconstructing it from chat.
- Build a non-instantiable dry-run execution-plan fixture from the unapproved pilot program and prove that approval gating prevents project creation/execution.
- Define the exact project-bootstrap payload that would be emitted after human approval.
- During vertical-slice validation, ingest multiple additional papers and require deeper novelty review before any candidate becomes SUPPORTED_AS_OPEN.
- Choose persistence/indexing architecture only after the complete vertical slice demonstrates actual query/load requirements.
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
