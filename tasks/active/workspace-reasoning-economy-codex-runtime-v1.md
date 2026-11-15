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
- Remote checkpoint: 164c039b73a1433370802d962eaf949a688eb0a5
- Remote verified: true

## Next safe action

DO NOT implement another bootstrap workflow: it already exists at exact head 164c039b73a1433370802d962eaf949a688eb0a5. First add tests/test_workspace_reasoning_economy_codex_runtime.py that statically prove the workflow preserves the frozen safety/resource contract (control-small only; no PADataset/GPU/Docker/sibling access; OPENAI_API_KEY unset; ChatGPT-only auth; Codex 0.155.1 + exact release digest; persistent paths only under Workspace Control home; zero model inference; redacted receipt; no capacity/root-policy widening). Then run repository validation on the exact candidate. If green, open/continue a stacked PR whose base is PR #627 head branch padataset-dual-science-control-reserve-v1 at acd420758eb0124646988ee8776939572c88a82d. Do not add or activate the live root route until the inert workflow is validated and promoted to an exact default-branch blob.

## Remaining work

- Add tests/test_workspace_reasoning_economy_codex_runtime.py with static contract tests for exact runner class, no GPU/Docker/sibling access, OPENAI_API_KEY stripping, ChatGPT-only auth, pinned Codex version/digest, no model inference, redacted receipt, and absence of capacity/root-authority widening.
- Repository-validate the inert bootstrap workflow candidate on the stacked branch; do not treat implementation presence as validation.
- Open/validate the Codex runtime PR stacked on PR #627 head padataset-dual-science-control-reserve-v1@acd420758eb0124646988ee8776939572c88a82d without modifying PR #627.
- Promote the validated inert workflow to default branch and bind its exact blob before adding any trusted route.
- Add and validate an additive /workspace-codex-bootstrap route on workspace-control-control-small-v1 while preserving host=3, PADataset=2, Workspace Control=1, reserved=1.
- Activate only through reviewed v3 root-policy/provisioner authority; no manual runner or sidecar bypass.
- Run zero-inference bootstrap; if login is absent, user performs one device-code ChatGPT authorization.
- Prove account.type=chatgpt, planType=plus, and programmatic rate-limit/usage reads without leaking credential/account identity material.
- Return to parent workspace-reasoning-economy-v1 codex_subscription_executor stage after runtime/auth preflight succeeds.

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
