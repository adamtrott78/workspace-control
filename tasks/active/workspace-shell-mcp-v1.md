<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-shell-mcp-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-shell-mcp-v1
- Title: Workspace Shell MCP v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Give ChatGPT durable, auditable, least-privilege command-execution access to the Lambda workspace through a separate private MCP/plugin so workspace-control tasks can execute and inspect bounded shell operations directly without using the operator as a copy/paste terminal relay, while preserving explicit provenance, credential isolation, rollback boundaries, and independently reviewable privileged authority.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: main
- Remote checkpoint: a802c417ffcc0bea604263ad029ed1b17f94656a
- Remote verified: true

## Current stage

freeze_authority_design_review_candidate — design review candidate, NOT accepted. GitHub-only historical/structural recovery completed; fresh live Lambda host attestation and independent design review still open.

## Design artifacts

- `architecture/workspace-shell-mcp-authority-v1.json`
- `procedures/workspace_shell_mcp_design_review.md`

## Next safe action

Review design candidate artifacts on the Workspace Shell design PR. Obtain independent immutable-head review and fresh read-only Lambda host attestation; resolve all blockers with a new exact-head review before implementation. No Lambda/Heartbeat mutation or shell activation.

## Remaining work

- Obtain fresh read-only host attestation without exposing secrets and reconcile with frozen candidate design.
- Validate exact task/design artifacts and request independent immutable-head review; address blocking findings.
- Only after accepted authority design, implement isolated, unprivileged policy-bound shell with adversarial tests.
- Review implementation and controlled rollback separately before any live installation or ChatGPT connection.
- Run isolated and later authorized live exact-SHA receipt acceptance; keep other project controllers untouched.

## Blockers / gates

- Live Lambda configuration and process identity remain unverified by fresh host attestation.
- Independent immutable-head authority/threat design review has not returned NO_BLOCKING_FINDING.
- Implementation, tunnel provisioning, privileged helper installation and service activation are prohibited.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-mcp-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
