<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-github-actions-selfhosted-control-plane-v1
- Title: GitHub Actions Self-Hosted Control Plane v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Eliminate routine dependence on metered GitHub-hosted runners by moving workspace-control and project CI onto bounded self-hosted Lambda execution while preserving a non-circular bootstrap authority, per-project isolation, fail-closed admission, review gates, and a clean path to GitHub organization runner groups. Also reduce operator copy/paste by making review targets and dispositions durable and GitHub-native.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: github-actions-selfhosted-control-plane-v1
- Baseline checkpoint: 3619574d8b10441fbec18f92ce7005d036aad7c8
- Remote verified: true

### research-engine

- Intent: read
- Remote branch: main
- Remote checkpoint: 15c2f98feb980f18fac255b74c6a39db5da4ef30
- Remote verified: true

## Current stage

freeze_control_plane_design

## Next safe action

Freeze the v0.1 control-plane architecture and a NOT_INSTALLED workspace-control JIT manifest, open a design-only PR, and request independent review. In parallel, once temporary public visibility or hosted capacity is available, rerun the authoritative reconciliation to unblock current EXTRACT validation without changing scientific authority.

## Key safety boundary

The existing Lambda reconciliation controller requires a successful trusted reconciliation workflow run before it will hydrate policy. Therefore the trusted bootstrap/reconciliation validator cannot simply be moved onto a dynamically reconciled runner that depends on that same policy. Preserve an independently recoverable bootstrap layer.

## Remaining work

- Freeze exact v0.1 architecture and NOT_INSTALLED workspace-control manifest.
- Obtain independent review of the design-only change.
- Restore the currently blocked reconciliation/EXTRACT validation chain using the temporary emergency capacity workaround.
- Implement and validate a bounded workspace-control self-hosted pilot without creating bootstrap circularity.
- Migrate routine hosted CI only after the pilot is accepted.
- Evaluate and separately execute GitHub organization migration with runner groups.
- Automate routine review request/consumption so the operator does not ferry text between chats.

## Fresh-chat initialization

@GitHub @Heartbeat

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
`tasks/active/workspace-github-actions-selfhosted-control-plane-v1.json`

Task ID:
`workspace-github-actions-selfhosted-control-plane-v1`

Start from the normal workspace-control root route.
Treat the authoritative task capsule, synchronized Markdown handoff, exact durable Git/runtime state, and referenced evidence as the complete handoff.
Do not rely on previous conversation state.
Immediately begin Workspace Heartbeat with the same real task ID.
Follow the capsule's `next_safe_action`.
Do not mutate Local EXTRACT science.
Do not activate a self-hosted control runner until the exact design receives independent review.
