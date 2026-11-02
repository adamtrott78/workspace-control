<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-github-actions-control-plane-protocol-redesign-v1
- Title: GitHub Actions Control-Plane Protocol Redesign v1
- Status: COMPLETE
- Capsule schema: v2

## Goal

Replace the current parser-chained GitHub Actions runner admission path with a formally modeled, versioned, typed control-plane protocol whose routing, authority, scheduling, provisioning, execution, recovery, and lifecycle semantics are explicit end-to-end, so any executor request admitted by policy cannot later be falsely rejected by a downstream parser that implements a different grammar.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 8129291a59be2b25fa837c81091a0d7d8cac3387
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

Task complete for the accepted production scope. Resume workspace-semantic-execution-migration-v1 immediately. Do not delete lambda-research-engine, lambda-research-engine-gpu, or preserved v2 controller bytes/config/state from this completed task; those require separate future Research acceptance/cleanup authority.

## Remaining work

None. The accepted GitRunner v3 production migration scope is complete.

## Blockers / gates

None for this completed task. Research legacy scale sets and preserved v2 controller bytes/config/state remain intentionally out of scope pending separate future authority.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.


## Completion evidence

- Production generation cutover accepted with transaction /var/lib/workspace-ci/v3/migration/358b3fb9-f702-401e-b6bd-69d8c89f3488/transaction.json.
- Legacy retirement receipt: /var/lib/workspace-ci/v3/legacy-retirement/fb427e98-2eaf-45d9-8392-e8f0757b8142/receipt.json.
- Retired: lambda-workspace-control id=3; lambda-padataset id=2; lambda-padataset-gpu id=1.
- Fresh-process verification proved the three legacy names absent and accepted v3 targets still present: lambda-workspace-control-control-small id=2; lambda-padataset-cpu-public id=3; lambda-padataset-gpu-single-public id=4.
- Research legacy scale sets remain preserved; all v2 controller bytes/config/state remain preserved for later authorized cleanup.
- Resume umbrella task workspace-semantic-execution-migration-v1.
