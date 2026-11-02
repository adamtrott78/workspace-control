<!-- workspace-control:derived-task-handoff -->
# Workspace Control Task Handoff

Derived human-readable view.

Authoritative capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

If this view disagrees with the JSON capsule or verified Git/runtime evidence, trust the capsule plus verified evidence.

## Task

- ID: workspace-github-actions-control-plane-protocol-redesign-v1
- Title: GitHub Actions Control-Plane Protocol Redesign v1
- Status: IN_PROGRESS
- Capsule schema: v2

## Goal

Replace the current parser-chained GitHub Actions runner admission path with a formally modeled, versioned, typed control-plane protocol whose routing, authority, scheduling, provisioning, execution, recovery, and lifecycle semantics are explicit end-to-end, so any executor request admitted by policy cannot later be falsely rejected by a downstream parser that implements a different grammar.

## Repositories

### workspace-control

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: e1a2d44bf24a3a7bf53d77baf0fc6170e4af0f15
- Remote verified: true

### research-engine

- Intent: mutate
- Remote branch: github-actions-control-plane-protocol-redesign-v1
- Remote checkpoint: 6165556086b73d2076f205f11ec7b988150f23dd
- Remote verified: true

### PADataset

- Intent: mutate
- Remote branch: main
- Remote checkpoint: d214b20471aac348bd28802596b92f81ee146b76
- Remote verified: true

## Next safe action

GPU canary #1 failed closed only on the incomplete GPU filesystem deny contract and rolled back cleanly. The corrected shared v3 runtime has now been installed transactionally at exact validated head e1a2d44bf24a3a7bf53d77baf0fc6170e4af0f15 with runtime digest 86a7c8e33d689b11ece5cd1456ff3af9e841ed6b62a84356e8727d9cd8e1b9da, provisioner restart PASS, and Research GPU containment preserved. BEFORE GPU attempt #2, independently attest the live runtime/provisioner/root state and no active v3 class/transient/resource residue through Workspace Shell/maintenance evidence. Then prepare/validate a PADataset GPU retry operator that is bound to the refreshed runtime override state and the already trusted main workflow blob 9311657f079aa1894d16d5e83ed0b18a813af487. Only after those checks may one NEW ACTIVATE_ONE_V3_CANARY authority be minted and exactly padataset-gpu-single-public-v1 retried. Do not reuse the authority from failed GPU canary #1. Do not repeat workspace-control or PADataset CPU canaries.

## Remaining work

- Independently attest live runtime override receipt/digest support as far as Workspace Shell permits, v3 reconciler active/exited, v3 provisioner active/running, all v3 class controllers/transients/resources absent, PADataset legacy lanes restored/healthy, and Research GPU containment preserved.
- Ensure the PADataset GPU live operator for attempt #2 uses the corrected runtime/verifier assumptions from e1a2d44bf24a3a7bf53d77baf0fc6170e4af0f15 and exact trusted workflow blob 9311657f079aa1894d16d5e83ed0b18a813af487 on PADataset main d214b20471aac348bd28802596b92f81ee146b76.
- Run exactly one fresh-authority padataset-gpu-single-public-v1 canary, observe immutable envelope success, then terminal rollback.
- Independently attest roots, v3 inactivity/no residue, exact v2 restoration, PADataset lane health, and Research GPU containment; record GPU acceptance durably.
- Then perform the single controlled production generation cutover, drain/quiesce v2, retarget accepted workflows to exact v3 scale-set names, activate accepted production v3 classes, validate production, move v2 DRAINING -> RETIRED while preserving rollback bytes/state, and later clean legacy state.
- Immediately resume workspace-semantic-execution-migration-v1 umbrella work after the v3/v2 infrastructure gate is accepted.

## Blockers / gates

- GPU canary remains unaccepted; failed run 41420426352 is historical and its consumed authority must never be reused.
- Before GPU attempt #2, the live runtime override installed by e1a2d44bf24a3a7bf53d77baf0fc6170e4af0f15 must be independently attested together with roots/provisioner/no-v3-residue state.
- The next GPU attempt requires a completely fresh one-shot ACTIVATE_ONE_V3_CANARY authority after all preflights.
- Research CPU remains separately gated; all Research GPU-derived classes remain inherited-contained and NO_BY_DEFAULT.
- Production v3 cutover/v2 retirement remains gated on accepted PADataset GPU canary and exact post-canary acceptance.

## Fresh-chat initialization

@GitHub

https://github.com/adamtrott78/workspace-control

Continue the durable workspace-control task defined by:
Task capsule: tasks/active/workspace-github-actions-control-plane-protocol-redesign-v1.json

Start from the normal workspace-control root route.
Treat the task capsule, exact durable Git/runtime state, and referenced owning context/evidence as the handoff.
Do not rely on previous conversation state.
Follow the capsule's next_safe_action.
