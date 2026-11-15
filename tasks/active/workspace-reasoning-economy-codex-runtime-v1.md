<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-reasoning-economy-codex-runtime-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-reasoning-economy-codex-runtime-v1
- Title: Workspace Reasoning Economy Codex Runtime v1
- Status: NEEDS_USER_DECISION
- Capsule schema: v2

## Goal

Add a bounded, CPU-only Codex runtime/bootstrap capability to the existing Workspace Control control-small runner class so Reasoning Economy can use the user's included ChatGPT Plus Codex allowance without API billing, GPU access, credential copying, or bypassing the v3 root allocator.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: workspace-reasoning-economy-codex-runtime-v1
- Remote checkpoint: 07198a81430a8ec20360b9060043ed238c59cb59
- Remote verified: true

## Next safe action

DO NOT modify, merge, retarget, or regress PR #627. The inert bootstrap workflow and six static safety/resource contract tests are repository-validated at exact child head 07198a81430a8ec20360b9060043ed238c59cb59 by Workspace Control Validation #2788, and authoritative stacked PR #630 targets PR #627 base acd420758eb0124646988ee8776939572c88a82d. Trusted-workflow promotion is now authority-gated on the PR #627 reserved-capacity lineage reaching default branch (or an explicit owning-task authorization for another provenance-preserving promotion path). Once that gate is satisfied, promote the inert workflow to default branch, bind its exact blob, and only then add the bounded /workspace-codex-bootstrap route.

## Remaining work

- Promote the validated inert workflow to default branch and bind its exact blob after the PR #627 lineage gate is satisfied.
- Add and validate an additive /workspace-codex-bootstrap route on workspace-control-control-small-v1 while preserving host=3, PADataset=2, Workspace Control=1, reserved=1.
- Activate only through reviewed v3 root-policy/provisioner authority; no manual runner or sidecar bypass.
- Run zero-inference bootstrap; if login is absent, user performs one device-code ChatGPT authorization.
- Prove account.type=chatgpt, planType=plus, and programmatic rate-limit/usage reads without leaking credential/account identity material.
- Return to parent workspace-reasoning-economy-v1 codex_subscription_executor stage after runtime/auth preflight succeeds.

## Blockers / gates

- Trusted-workflow promotion is authority-gated on PR #627 lineage: authoritative stacked PR #630 targets padataset-dual-science-control-reserve-v1@acd420758eb0124646988ee8776939572c88a82d, while this child is explicitly prohibited from modifying, merging, retargeting, or regressing PR #627. The smallest next action is for the owner of PR #627 promotion authority to land/advance that reserved-capacity base to default branch, or explicitly authorize another provenance-preserving promotion path.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-reasoning-economy-codex-runtime-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
