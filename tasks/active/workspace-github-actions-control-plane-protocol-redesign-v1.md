<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-github-actions-control-plane-protocol-redesign-v1
- Title: GitHub Actions Control-Plane Protocol Redesign v1
- Status: ACTIVE
- Capsule schema: v2

## Goal

Replace the current parser-chained GitHub Actions runner admission path with a formally modeled, versioned, typed control-plane protocol whose routing, authority, scheduling, provisioning, execution, recovery, and lifecycle semantics are explicit end-to-end, so any executor request admitted by policy cannot later be falsely rejected by a downstream parser that implements a different grammar.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: f62a71bc4488da2cf2afeb90325d0b24dd61ada1
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 6165556086b73d2076f205f11ec7b988150f23dd
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: a8f952c7cf964730a01b2dc5c6cd75850912f94f
- Remote verified: true

## Next safe action

Validate the final task-bound PR #600 head. If green, issue a fresh authority-sensitive review request covering only the v3 controller binary refresh/restart and automatic queued-unbound reconciliation of #389; prohibit manual ledger mutation and all v2/PADataset/Research/scale-set/workflow/provisioner/reconciler changes.

## Remaining work

- Validate final task-bound PR #600 head through hosted Workspace Control Validation.
- Obtain fresh independent authority-sensitive review of exact repair head and bounded controller-only live recovery.
- Build/install only the reviewed v3 controller binary and restart only workspace-ci-v3-controller@workspace-control-control-small-v1.service under exact preflight/rollback.
- Verify the corrected controller reopens stale terminal #389 from exact queued/unbound GitHub evidence with a fresh provision identity and does not attribute competing lifecycle events.
- Record #389 terminal result and prove v3 class/controller/root ledger returns clean with no nonterminal residue.

## Blockers / gates

- Final exact-head hosted validation is required after this durable task-state binding.
- Fresh authority-sensitive review is required before replacing or restarting the live v3 workspace-control-control-small controller.
- No manual edit/delete/reset of scheduler-130058639814.json is authorized; recovery must be produced by the reviewed controller from exact GitHub queued/unbound evidence.
- Do not start or repair the retired legacy v2 workspace-control controller or recreate lambda-workspace-control.
- Do not mutate PADataset, Research Engine, v3 provisioner/reconciler, scale sets, workflows, root policy, or admission/capacity policy as part of this repair.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
