# Workspace Control Plane v2 — Current Handoff

> **Derived human-readable view.**
>
> Authoritative task state: `tasks/active/control-plane-v2-refactor.json` on `control-plane-v2-coordination`.
>
> If this file disagrees with the v2 JSON capsule or verified Git/runtime state, trust the JSON capsule plus verified evidence.

## Task

- ID: `control-plane-v2-refactor`
- Schema: `v2`
- Status: `CHECKPOINTED`
- Current stage: `phase11_codex_rerun`
- Execution topology: `remote_only`

## Frozen implementation

- Repository: `workspace-control`
- Branch: `control-plane-v2-refactor`
- Checkpoint: `b8aa52e242a07e6aa2036516e401864991183ad2`
- Remote verified: `true`

## Preserved history

The complete final v1 coordination history is preserved at:

`tasks/evidence/control-plane-v2-refactor-v1-final.json`

Do not reconstruct prior phase evidence from conversation memory.

## Completed gates

- Phase 10 regression matrix: `PASS`
- MILCOM real-workflow reference regression: `PASS`
- Phase 11 exact integration diff review: `PASS`
- Phase 11 v1 compatibility review: `PASS`

## Pending Phase 11 gates

- validate this v2 capsule and prove `HANDOFF_SAFE`;
- rerun ChatGPT -> Codex -> ChatGPT handoff against this exact v2 state;
- obtain explicit user promotion decision;
- if approved, transition to `COMPLETE`, promote the reviewed checkpoint, and verify final state.

## Next safe action

Validate the active v2 capsule and HANDOFF_SAFE state against control-plane-v2-refactor@b8aa52e242a07e6aa2036516e401864991183ad2, then perform the required both-direction Codex handoff rerun. Do not promote until those gates pass and the user explicitly approves promotion.

## Fresh-chat initialization

```text
@GitHub

Continue the durable workspace-control v2 promotion task.

Repository:
adamtrott78/workspace-control

Coordination branch:
control-plane-v2-coordination

Authoritative capsule:
tasks/active/control-plane-v2-refactor.json

Derived handoff:
tasks/active/control-plane-v2-refactor.md

Preserved v1 history:
tasks/evidence/control-plane-v2-refactor-v1-final.json

Frozen target:
control-plane-v2-refactor@b8aa52e242a07e6aa2036516e401864991183ad2

Treat the v2 JSON capsule and verified Git/runtime evidence as authoritative.
Do not rely on prior conversation memory.
Do not promote until Phase 11 v2 HANDOFF_SAFE, Codex round-trip, and explicit user approval all pass.
```
