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
- Remote branch: workspace-shell-mcp-v1-design-freeze
- Remote checkpoint: cc37231f7c88d65f564b3357ce679e2035e153d8
- Remote verified: true

## Next safe action

Validate PR #550 at the corrected exact head. If validation passes, record a fresh independent review request bound to that immutable head for the frozen authority/threat design. Do not implement, install, provision a tunnel/key, create a sudo/root helper, or mutate Lambda until the applicable review gates are satisfied.

## Remaining work

- Validate the corrected task capsule/handoff and frozen design artifacts on PR #550.
- Request fresh independent review against the exact immutable PR head and resolve every blocking finding.
- After design acceptance, implement the isolated unprivileged server/policy and root-helper broker in repository only, with adversarial tests; no live Lambda authority yet.
- Obtain fresh read-only Lambda host attestation before host-specific installation design is finalized.
- Independently review implementation and installation/rollback boundary before provisioning a dedicated tunnel credential or live service.
- Run isolated acceptance, then separately authorize live exact-SHA/receipt acceptance while keeping Heartbeat and unrelated project controllers untouched.

## Blockers / gates

- Independent immutable-head authority/threat design review has not returned NO_BLOCKING_FINDING.
- Fresh live Lambda host attestation remains required before installation or activation; repository evidence alone is not host attestation.
- Implementation is blocked until design review; tunnel provisioning, privileged helper installation and live service activation are separately prohibited until later gates.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-mcp-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
