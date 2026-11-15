<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-reasoning-economy-codex-runtime-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-reasoning-economy-codex-runtime-v1
- Title: Workspace Reasoning Economy Codex Runtime v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Add a bounded, CPU-only Codex runtime/bootstrap capability to the existing Workspace Control control-small runner class so Reasoning Economy can use the user's included ChatGPT Plus Codex allowance without API billing, GPU access, credential copying, or bypassing the v3 root allocator.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-reasoning-economy-codex-runtime-v1
- Remote checkpoint: acd420758eb0124646988ee8776939572c88a82d
- Remote verified: true

## Next safe action

Implement the inert lambda-ci-workspace-control-codex-bootstrap.yml workflow on this stacked branch. Reuse the exact same-repository PR-head and control-small isolation gates from the accepted control-validation workflow; pin Codex 0.155.1 and its official SHA-256; write runtime/CODEX_HOME only under the Workspace Control project home; force ChatGPT auth; perform no model inference; emit only a redacted receipt. Add static tests proving no API key, GPU, sibling-project, or capacity widening behavior. Do not add the live root route until this workflow is validated and promoted to an exact default-branch blob.

## Remaining work

- Implement and repository-validate the inert pinned Codex bootstrap workflow.
- Promote the inert workflow to main and bind its exact blob.
- Add and validate the bootstrap route on the existing control-small class while preserving PR #627 capacity invariants.
- Activate the additive route through the reviewed v3 root-policy mechanism.
- Run bootstrap; if needed perform one device-code ChatGPT authorization.
- Prove Plus auth and programmatic account/rate-limit/usage reads with zero model inference.

## Blockers / gates

- None.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-reasoning-economy-codex-runtime-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
