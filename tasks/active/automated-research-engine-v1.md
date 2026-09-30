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
- Remote checkpoint: ca1c5a45facbed732aca3f40a3de53e4b6d8f4df
- Remote verified: true

## Next safe action

Continue proposal_compiler from automated-research-engine-v1@ca1c5a45facbed732aca3f40a3de53e4b6d8f4df. Define ResearchProgram, FundingOpportunity, SolicitationRequirement, and ProposalCompilation contracts. Use only a NOT_FOR_SUBMISSION dry-run fixture because the current surviving RF OSR candidate is NARROWED and requires deeper prior-work review; do not select it as the user's research direction and do not mark it fundable/novel.

## Remaining work

- Define ResearchProgram and solicitation/proposal compiler contracts without treating a NARROWED/NEEDS_HUMAN_REVIEW gap as an approved research direction.
- Build a dry-run proposal compilation fixture that demonstrates evidence mapping and required human gates but is explicitly NOT_FOR_SUBMISSION.
- Add official funding-opportunity adapter contracts and solicitation requirement mapping.
- Build the execution bridge from an APPROVED research program into a workspace-control project/task workflow.
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
