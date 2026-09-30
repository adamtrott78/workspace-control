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
- Remote checkpoint: 7f40545ac0ccf891d8a108a6b83180eb9f5b5428
- Remote verified: true

## Next safe action

Provide the exact locally acquired /tmp/research-engine-2108.13099v1.pdf to the current extraction executor (prefer direct file upload). Verify its SHA-256 is 7fcfc9929fd80a94095657ebf644be3301000d0a4342b74de1adc2af529ff7ab before extraction. Then parse the full PDF with stable page/section/block locators and create a new FULLTEXT_PDF_* extraction fixture that supersedes, but does not overwrite, the ABSTRACT_ONLY baseline.

## Remaining work

- Make the exact acquired PDF artifact for arXiv 2108.13099v1 accessible to the extraction executor and verify its SHA-256 against 7fcfc9929fd80a94095657ebf644be3301000d0a4342b74de1adc2af529ff7ab.
- Parse that exact PDF into a normalized document representation with page/section/block locators.
- Create a full-text typed evidence fixture covering research question, methods, experiments, dataset, metrics, quantitative results, and limitations/assumptions where present.
- Manually verify a benchmark subset of source locators and numerical values.
- Extend extraction to several additional deep-read pilot papers to test schema generality.
- Choose persistence/indexing architecture only after real ingress/extraction objects demonstrate storage/query requirements.
- Build provenance-preserving synthesis, contradiction handling, gap generation, and adversarial novelty challenge.
- Build the research-program/funding/proposal layer and explicit human gates.
- Bridge an approved research program into a workspace-control project execution workflow.

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
