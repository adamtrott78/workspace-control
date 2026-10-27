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
- Remote checkpoint: c28671e3e571cba298e8341bbce6999edc62bfd3
- Remote verified: true

## Next safe action

After this state-only synchronization passes validation, record a fresh immutable-head independent re-review request on PR #550 that consumes blocking review 6447046381 and cites corrected design checkpoint c28671e3e571cba298e8341bbce6999edc62bfd3 / validation run #990. Do not implement, merge, install, provision tunnel/key, create job-launcher/root-broker/helper authority, execute Lambda commands, modify Heartbeat, or mutate project controllers.

## Remaining work

- Validate the BF-1/BF-2 corrected authority artifact, review procedure, task capsule and synchronized handoff on PR #550.
- Record a fresh corrected-head independent review request consuming blocking review 6447046381 and resolve every new finding.
- Only after design acceptance, implement repository-only policy frontend, job-launcher protocol, hostile worker sandbox, approval verifier and reviewed-helper broker with adversarial tests; no live Lambda authority yet.
- Obtain fresh read-only Lambda host attestation before finalizing host-specific installation units/UIDs/sockets/mounts and approval trust-store placement.
- Independently review implementation and installation/rollback boundary before provisioning a dedicated tunnel credential or live service.
- Run isolated acceptance and later separately authorized live exact-SHA/receipt acceptance while keeping Heartbeat and unrelated project controllers untouched.

## Blockers / gates

- Fresh independent immutable-head review has not yet accepted the BF-1/BF-2 corrected authority/threat design.
- Fresh live Lambda host attestation remains required before installation or activation; repository evidence alone is not host attestation.
- Implementation, tunnel/key provisioning, job-launcher/root-broker/helper installation and live service activation remain prohibited until later gates.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-shell-mcp-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
