<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/automated-research-engine-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: automated-research-engine-v1
- Title: Automated research engine v1
- Status: BLOCKED_RUNTIME
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
- Remote checkpoint: 7dc229243e223438bc860946988977aa4f8d54f2
- Remote verified: true

## Next safe action

Run the documented noninteractive local acquisition command for arXiv 2108.13099v1 and return its receipt (URL, byte count, SHA-256, and PDF magic). Do not rerun discovery or identity resolution. After receipt, record a successful AcquisitionAttempt, clear BLOCKED_RUNTIME, validate ingress_prototype, and advance to extraction_pipeline.

## Remaining work

- Acquire and cryptographically hash at least one lawful OA full-text artifact using a runtime/tool with byte retrieval access; record both the successful acquisition and prior failed executor attempt.
- Validate the ingress schemas and pilot fixtures mechanically in the future research-engine implementation repository.
- Build normalized parsing and typed evidence extraction with source locators and verification state.
- Choose persistence/indexing architecture only after real ingress/extraction objects demonstrate storage/query requirements.
- Build provenance-preserving synthesis, contradiction handling, gap generation, and adversarial novelty challenge.
- Build the research-program/funding/proposal layer and explicit human gates.
- Bridge an approved research program into a workspace-control project execution workflow.
- Run the narrow-domain vertical slice and measure evidence fidelity, traceability, novelty false-positive rate, and execution handoff quality.

## Blockers / gates

- Current ChatGPT container cannot resolve external hosts for byte acquisition (curl to arxiv.org failed with DNS resolution error). The lawful OA source is resolved and readable through the scholarly/web surface; only byte retrieval/hash evidence is missing.

## Fresh-chat initialization

@GitHub

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/automated-research-engine-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
